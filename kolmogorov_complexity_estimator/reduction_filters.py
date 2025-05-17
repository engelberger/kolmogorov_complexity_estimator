# Pre-run and runtime non-halting detectors, symmetry logic 
from typing import Dict, Tuple
from .tm_constants import HALT_STATE
from collections import deque, Counter


def has_no_halt_transition(
    tm_table: Dict[Tuple[int, str], Tuple[int, str, int]]
) -> bool:
    """
    Check if the transition table contains no transition to the halt state.

    :param tm_table: Mapping from (state, read_symbol) to (next_state, write_symbol, move_code)
    :return: True if no transitions lead to HALT_STATE, False otherwise.
    """
    # Iterate through all transitions to find halt state
    for next_state, _, _ in tm_table.values():
        if next_state == HALT_STATE:
            return False
    return True 

def check_for_escapee(tm) -> bool:
    """
    Detect escapee: TM moving over fresh blank cells consecutively more than its number of states.
    Returns True to signal the machine is escaping.
    """
    # Initialize escapee tracking attributes
    if not hasattr(tm, '_escapee_seen_positions'):
        # Track positions visited for escape detection
        tm._escapee_seen_positions = {tm.head_position}
        tm._escapee_blank_run_count = 0
        return False
    # Determine if current head pos is a new blank cell (use defaultdict to detect blank)
    current_pos = tm.head_position
    is_blank = tm.tape[current_pos] == tm.blank_symbol
    is_new = current_pos not in tm._escapee_seen_positions
    if is_blank and is_new:
        tm._escapee_blank_run_count += 1
        tm._escapee_seen_positions.add(current_pos)
    else:
        tm._escapee_blank_run_count = 0
    # If run over fresh blank cells exceeds number of states, it's an escapee
    if tm._escapee_blank_run_count > tm.num_states:
        return True
    return False 

def check_for_cycle_two(tm) -> bool:
    """
    Detect 2-step cycles: if at steps s and s+2 the (state, head_position, tape) are identical.
    Returns True to signal the machine is caught in a period-two loop.
    """
    # Initialize or reset history if missing or invalid
    if not hasattr(tm, '_cycle_history') or tm._cycle_history is None:
        tm._cycle_history = deque(maxlen=3)
    # Capture current configuration: (state, head_position, tape contents)
    tape_snapshot = frozenset(tm.tape.items())
    config = (tm.current_state, tm.head_position, tape_snapshot)
    tm._cycle_history.append(config)
    # When we have at least 3 configs, compare first and last for period-2 cycle
    if len(tm._cycle_history) == 3 and tm._cycle_history[0] == tm._cycle_history[2]:
        return True
    return False 

def apply_completion_rules(
    output_counts: Counter,
    non_halting_count: int,
    M_red: int,
    n_states: int
) -> Tuple[Counter, int, int, int]:
    """
    Complete output and non-halting counts after running M_red machines in reduced enumeration.

    Steps:
    1. Right-left symmetry: add reversed strings and double non-halting count.
    2. Initial transitions to halt: add subspace_size runs of '0' and '1'.
    3. Initial self-transitions: add 4*subspace_size non-halting runs.
    4. Blank symbol symmetry: complement strings and double non-halting count again.

    Returns:
        total_counts: Counter of final output strings counts.
        total_non_halting: final non-halting count.
        effective_halting: total halting machines (sum counts).
        effective_total: sum of halting and non-halting machines.
    """
    # Base for subspace: number of tail combos per initial code
    subspace_size = M_red // (2 * (n_states - 1))

    # Step 1: right-left symmetry
    total_counts = Counter(output_counts)
    for s, c in output_counts.items():
        total_counts[s[::-1]] += c
    non_halting = non_halting_count * 2

    # Step 2: initial transitions to halt (write '0' or '1')
    total_counts['0'] += subspace_size
    total_counts['1'] += subspace_size

    # Step 3: initial self-transitions (state->itself with L/R)
    non_halting += 4 * subspace_size

    # Step 4: blank symbol symmetry via complement
    complement_map = {'0': '1', '1': '0'}
    complemented = Counter()
    for s, c in total_counts.items():
        comp = ''.join(complement_map.get(ch, ch) for ch in s)
        complemented[comp] += c
    # Combine original and complemented
    total_counts += complemented
    non_halting *= 2

    effective_halting = sum(total_counts.values())
    effective_total = effective_halting + non_halting
    return total_counts, non_halting, effective_halting, effective_total 