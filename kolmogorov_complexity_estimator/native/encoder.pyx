# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
"""
Cython module for TM encoding/decoding.
"""

# For native int_to_tm_table, import constants directly or define them
# Assuming SYMBOLS = ['0', '1'] and MOVES = {'L': -1, 'R': 1, 'N': 0}, HALT_STATE = 0

# C-level constants (mirroring tm_constants.py)
DEF HALT_STATE_C = 0
DEF MOVE_L_C = -1
DEF MOVE_R_C = 1
DEF MOVE_N_C = 0
DEF NUM_SYMBOLS_C = 2 # SYMBOLS = ['0', '1']

# SYMBOLS as Python strings for dict keys/values
cdef list SYMBOLS_PY = ['0', '1']


# Helper to encode a single TM transition into its integer code (Cython version)
# This is an internal helper, not a cpdef function
cdef int _encode_transition_cy(\
    int next_state_c, bytes write_symbol_b, int move_code_c, int n_states) except? -1:
    # No error checking here, assume valid inputs from tm_to_int_cy
    # This function is performance critical.
    cdef int write_idx, move_idx

    if next_state_c == HALT_STATE_C:
        if write_symbol_b == b'0': # SYMBOLS_PY[0]
            return 0
        else: # write_symbol_b == b'1', SYMBOLS_PY[1]
            return 1
    else:
        # Active state entries
        if write_symbol_b == b'0': # SYMBOLS_PY[0]
            write_idx = 0
        else: # write_symbol_b == b'1', SYMBOLS_PY[1]
            write_idx = 1
        
        if move_code_c == MOVE_L_C:
            move_idx = 0
        else: # move_code_c == MOVE_R_C:
            move_idx = 1
        
        # Compute code offset: 2 + 4*(state-1) + write_idx*2 + move_idx
        # (next_state_c - 1) is 0-indexed state for calculation
        return 2 + (next_state_c - 1) * (NUM_SYMBOLS_C * 2) + (write_idx * 2 + move_idx)

cpdef long tm_to_int(dict tm_table, int n_states):
    """
    Encode a full Turing machine transition table as an integer. (Cython optimized)
    """
    cdef int base = 4 * n_states + 2
    cdef long number = 0
    cdef int state, sym_idx, code
    cdef tuple transition_val_py
    cdef int next_state_c, move_code_c
    cdef bytes write_symbol_b # Use bytes for _encode_transition_cy

    # Build digits (big-endian) and combine into integer
    # Loop order must match int_to_tm_table's decoding order
    for state in range(1, n_states + 1):
        for sym_idx in range(NUM_SYMBOLS_C):
            # tm_table keys are (state_int, symbol_str)
            # tm_table values are (next_state_int, symbol_str, move_code_int)
            transition_val_py = tm_table[(state, SYMBOLS_PY[sym_idx])]
            
            next_state_c = transition_val_py[0]
            # Convert Python string symbol to bytes for helper
            if transition_val_py[1] == '0':
                write_symbol_b = b'0'
            else:
                write_symbol_b = b'1'
            move_code_c = transition_val_py[2]

            code = _encode_transition_cy(next_state_c, write_symbol_b, move_code_c, n_states)
            
            # This check should ideally not be needed if _encode_transition_cy is correct
            # and inputs are validated beforehand (e.g. in a Python wrapper if this is called directly)
            # if not (0 <= code < base):
            #     # Handle error or raise exception
            #     pass

            number = number * base + code
            
    return number


cpdef dict int_to_tm_table(long number, int n_states):
    """Decode an integer into a TM transition table using Cython for speed."""
    cdef dict tm_table = {}
    cdef int base = 4 * n_states + 2
    cdef int total_entries = 2 * n_states

    cdef int[20] digits  # Max n_states around 5-6 -> total_entries = 10-12. Static array.
                         # If n_states can be much larger, dynamic allocation would be needed.
    cdef int i
    cdef long remainder = number
    
    # Extract digits (least significant first into digits array)
    for i in range(total_entries): # digits[0] will be least significant
        digits[i] = remainder % base
        remainder //= base
    
    # Process digits (most significant first for table construction)
    # The digits were extracted LSB first, so now we read from the end of the array.
    cdef int current_digit_idx = total_entries - 1
    cdef int state, sym_idx_c, code, next_state_c, move_code_c
    cdef int combos_per_state_action, state_offset_idx, inner_combo_idx, write_idx_c, move_idx_c
    cdef str write_symbol_py # Python string versions for dict value

    for state in range(1, n_states + 1):
        for sym_idx_c in range(NUM_SYMBOLS_C): # Iterate 0 for '0', 1 for '1'
            code = digits[current_digit_idx]
            current_digit_idx -= 1

            key_tuple = (state, SYMBOLS_PY[sym_idx_c])

            if code < NUM_SYMBOLS_C: # Codes 0, 1 for HALT_STATE
                next_state_c = HALT_STATE_C
                write_symbol_py = SYMBOLS_PY[code] 
                move_code_c = MOVE_N_C
            else:
                # Active state entry: code from NUM_SYMBOLS_C up to base-1
                offset_code = code - NUM_SYMBOLS_C # Adjust code to be 0-indexed for calculation
                
                combos_per_state_action = NUM_SYMBOLS_C * 2 # Number of (write_symbol, move) combos for an active state = 2 * 2 = 4
                
                state_offset_idx = offset_code // combos_per_state_action # Determines next_state (0-indexed)
                inner_combo_idx = offset_code % combos_per_state_action  # Determines write_symbol and move
                
                next_state_c = state_offset_idx + 1 # Convert back to 1-indexed state
                
                write_idx_c = inner_combo_idx // 2 # 0 for '0', 1 for '1'
                move_idx_c = inner_combo_idx % 2   # 0 for 'L', 1 for 'R'

                write_symbol_py = SYMBOLS_PY[write_idx_c]
                if move_idx_c == 0:
                    move_code_c = MOVE_L_C
                else: # move_idx_c == 1
                    move_code_c = MOVE_R_C
            
            tm_table[key_tuple] = (next_state_c, write_symbol_py, move_code_c)
    
    return tm_table 