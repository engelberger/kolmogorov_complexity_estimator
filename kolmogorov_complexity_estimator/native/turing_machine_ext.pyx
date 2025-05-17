"""
Cython module for optimized TuringMachine step and runtime filters.
"""

from ..tm_constants import HALT_STATE #, BLANK_SYMBOL_DEFAULT # Not directly used here yet
from collections import defaultdict, deque # For type hints and fallback attributes

# We operate on the Python TuringMachine object directly for now.
# For maximal speed, one might cdef a Cython class mirroring TuringMachine attributes,
# but that's a larger refactor. Accessing Python object attributes from Cython is feasible.

cpdef int cython_step(object tm_obj) except? -2:
    """
    Optimized Cython version of TuringMachine.step. 
    Returns 1 to continue, 0 to halt, -1 on error (e.g., missing transition).
    Directly manipulates attributes of the passed Python TuringMachine object.
    """
    # Type casting for attribute access (no C-level struct here)
    # This still involves Python object interaction but avoids Python bytecode for the logic itself.
    cdef int current_state = tm_obj.current_state
    cdef dict transition_table = tm_obj.transition_table
    cdef object tape = tm_obj.tape # tape is defaultdict
    cdef int head_position = tm_obj.head_position
    # tm_obj.blank_symbol is not directly used in step logic if tape handles it

    if current_state == HALT_STATE:
        return 0 # Halt

    # Read current symbol - tape[head_position] will call defaultdict logic
    current_symbol = tape[head_position] 
    key = (current_state, current_symbol)

    if key not in transition_table:
        tm_obj.current_state = HALT_STATE # Transition to HALT if undefined
        return 0 # Halt

    # Apply transition
    # transition_val is (next_state, write_symbol, move_code)
    transition_val = transition_table[key]
    next_state_c = transition_val[0]
    write_symbol_py = transition_val[1]
    move_code_c = transition_val[2]

    tape[head_position] = write_symbol_py # Write to tape (still defaultdict access)
    tm_obj.current_state = next_state_c   # Update state
    new_head_position = head_position + move_code_c
    tm_obj.head_position = new_head_position # Move head

    # Update visited range (Python attribute access)
    tm_obj.min_visited = min(tm_obj.min_visited, new_head_position)
    tm_obj.max_visited = max(tm_obj.max_visited, new_head_position)
    
    tm_obj.steps_taken += 1 # Increment step counter

    if next_state_c == HALT_STATE:
        return 0 # Halt
    
    return 1 # Continue


cpdef bint check_escapee(object tm_obj):
    """Optimized Cython version of check_for_escapee."""
    # Accessing attributes that might be created on the fly in Python version
    if not hasattr(tm_obj, "_escapee_seen_positions"):
        tm_obj._escapee_seen_positions = {tm_obj.head_position}
        tm_obj._escapee_blank_run_count = 0
        return False

    cdef set seen_positions = tm_obj._escapee_seen_positions
    cdef int current_pos = tm_obj.head_position
    is_blank = tm_obj.tape[current_pos] == tm_obj.blank_symbol
    is_new = current_pos not in seen_positions

    if is_blank and is_new:
        tm_obj._escapee_blank_run_count += 1
        seen_positions.add(current_pos) # Modify the set on Python object
    else:
        tm_obj._escapee_blank_run_count = 0
    
    if tm_obj._escapee_blank_run_count > tm_obj.num_states:
        return True
    return False


cpdef bint check_cycle_two(object tm_obj):
    """Optimized Cython version of check_for_cycle_two."""
    if not hasattr(tm_obj, "_cycle_history") or tm_obj._cycle_history is None:
        tm_obj._cycle_history = deque(maxlen=3)
    
    cdef object history = tm_obj._cycle_history
    # Tape snapshot still involves Python dict items and frozenset creation
    # This part will remain relatively Python-heavy unless tape is also C-level
    tape_snapshot = frozenset(tm_obj.tape.items())
    config = (tm_obj.current_state, tm_obj.head_position, tape_snapshot)
    
    history.append(config)
    
    if len(history) == 3 and history[0] == history[2]:
        return True
    return False 