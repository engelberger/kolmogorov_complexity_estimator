# Generators for raw and reduced TM sets
from typing import Dict, Generator, Tuple

from .tm_constants import SYMBOLS
from .tm_encoder import int_to_tm_table


def generate_raw_tm_tables(
    num_states: int, num_symbols: int = 2
) -> Generator[Dict[Tuple[int, str], Tuple[int, str, int]], None, None]:
    """
    Generate all possible Turing machine transition tables for given num_states and
    num_symbols. Uses integer enumeration and int_to_tm_table for decoding.

    :param num_states: Number of non-halting states (states 1..num_states).
    :param num_symbols: Number of tape symbols (must match configured SYMBOLS length).
    :yield: A transition table dict mapping (state, symbol) to (next_state,
            write_symbol, move_code).
    """
    # Ensure supported symbol count
    if num_symbols != len(SYMBOLS):
        raise ValueError(
            f"Only {len(SYMBOLS)} symbols supported, " f"got num_symbols={num_symbols}"
        )
    base = 4 * num_states + 2
    total_entries = num_states * num_symbols
    max_number = pow(base, total_entries)
    for code in range(max_number):
        # Decode the integer to a transition table
        tm_table = int_to_tm_table(code, num_states)
        yield tm_table


def generate_reduced_tm_tables(
    num_states: int, num_symbols: int = 2
) -> Generator[Dict[Tuple[int, str], Tuple[int, str, int]], None, None]:
    """
    Generate a reduced set of Turing machine transition tables by symmetry:
    only machines whose initial transition (state 1 reading the blank symbol)
    moves right to a non-initial (state>1), non-halting state.

    Total machines: 2*(num_states-1)*(base^(2*num_states-1)), where base=4*num_states+2.
    """
    # Ensure supported symbol count
    if num_symbols != len(SYMBOLS):
        raise ValueError(
            f"Only {len(SYMBOLS)} symbols supported, " f"got num_symbols={num_symbols}"
        )
    base = 4 * num_states + 2
    entry_count = num_states * num_symbols
    # Number of tail combinations after the first entry
    subspace_size = pow(base, entry_count - 1)
    # Build allowed initial codes for (state=1, blank_symbol)
    allowed_initial_codes = []
    for next_state in range(2, num_states + 1):
        for write_symbol in SYMBOLS:
            write_idx = SYMBOLS.index(write_symbol)
            # move_idx for 'R' is 1
            code = 2 + (next_state - 1) * (len(SYMBOLS) * 2) + (write_idx * 2 + 1)
            allowed_initial_codes.append(code)
    # Enumerate all reduced machines
    for initial_code in allowed_initial_codes:
        offset = initial_code * subspace_size
        for tail in range(subspace_size):
            number = offset + tail
            tm_table = int_to_tm_table(number, num_states)
            yield tm_table

# New functions to yield TM numbers (integers) directly

def generate_tm_numbers(
    num_states: int, num_symbols: int = 2
) -> Generator[int, None, None]:
    """
    Generate integers representing all possible Turing machines.
    """
    if num_symbols != len(SYMBOLS):
        raise ValueError(
            f"Only {len(SYMBOLS)} symbols supported, got num_symbols={num_symbols}"
        )
    base = 4 * num_states + 2
    total_entries = num_states * num_symbols
    max_number = pow(base, total_entries)
    for code in range(max_number):
        yield code

def generate_reduced_tm_numbers(
    num_states: int, num_symbols: int = 2
) -> Generator[int, None, None]:
    """
    Generate integers representing a reduced set of Turing machines by symmetry.
    (Same logic as generate_reduced_tm_tables but yields numbers).
    """
    if num_symbols != len(SYMBOLS):
        raise ValueError(
            f"Only {len(SYMBOLS)} symbols supported, got num_symbols={num_symbols}"
        )
    base = 4 * num_states + 2
    entry_count = num_states * num_symbols
    subspace_size = pow(base, entry_count - 1)

    allowed_initial_codes = []
    # Assuming SYMBOLS = ['0', '1'] and blank symbol is SYMBOLS[0]
    # The initial transition is (state=1, blank_symbol)
    # Must move right (move_code_idx = 1 for R)
    # Next state must be > 1 and not HALT_STATE (0)
    # So next_state is in range(2, num_states + 1)

    # Logic from native.encoder._encode_transition_cy for next_state > 0:
    # code = 2 + (next_state_c - 1) * (NUM_SYMBOLS_C * 2) + (write_idx * 2 + move_idx)
    # Here, next_state_c is 1-indexed.
    # write_idx can be 0 or 1. move_idx for 'R' is 1.

    for next_s in range(2, num_states + 1): # next_state_c
        for write_s_idx in range(len(SYMBOLS)): # write_idx
            # move_idx for 'R' is 1 (if MOVES = {'L':0, 'R':1} in encoding)
            # or determined by actual move code if different.
            # Using the _encode_transition_cy logic:
            # (next_state_c - 1) is 0-indexed state for calculation
            # code = 2 + (next_state_c - 1) * (len(SYMBOLS) * 2) + (write_s_idx * 2 + 1) # 1 for 'R'
            # This is the code for ONE transition.
            # The "initial_code" in generate_reduced_tm_tables refers to the first "digit"
            # in the base-(4n+2) representation of the TM number.
            # This first digit corresponds to the transition for (state=1, SYMBOLS[0]) if a fixed
            # order is used for constructing the number from the table.

            # Let's replicate the logic used in generate_reduced_tm_tables's initial_code calculation.
            # It depends on how int_to_tm_table and tm_to_int order the transitions.
            # Assuming tm_to_int iterates state 1..n, then symbol 0..m-1.
            # So the first digit corresponds to (state=1, symbol=SYMBOLS[0]).
            # The code for this single transition:
            # next_state = next_s (2 to n_states)
            # write_symbol = SYMBOLS[write_s_idx]
            # move = 'R'

            # Let's use the definition from the existing generate_reduced_tm_tables for initial_code
            # This assumed:
            # code = 2 + (next_state - 1) * (len(SYMBOLS) * 2) + (write_idx * 2 + 1)
            # where next_state is 1-indexed.
            initial_transition_code = 2 + (next_s - 1) * (len(SYMBOLS) * 2) + (write_s_idx * 2 + 1)
            allowed_initial_codes.append(initial_transition_code)

    for initial_code_val in allowed_initial_codes:
        # The 'initial_code_val' is the most significant digit if the number is constructed
        # by digits = [d_2n-1, d_2n-2, ..., d_0] and number = sum(d_i * base^i).
        # Or, if number = (...((d_N * base + d_{N-1})*base + ...)*base + d_0),
        # then initial_code_val is d_N.
        # The current int_to_tm_table extracts LSB first, then processes MSB.
        # tm_to_int effectively does number = number * base + code, so MSB is added first.
        # The enumeration order in tm_to_int is:
        # for state in 1..n: for sym_idx in 0..NUM_SYMBOLS_C-1: code = ...; number = number * base + code
        # So the transition for (state=1, SYMBOLS[0]) is the first code incorporated.
        # This corresponds to the most significant digit.
        offset = initial_code_val * subspace_size
        for tail in range(subspace_size):
            number = offset + tail
            yield number
