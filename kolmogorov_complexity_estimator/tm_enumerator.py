# Generators for raw and reduced TM sets 
from typing import Dict, Generator, Tuple
from .tm_encoder import int_to_tm_table
from .tm_constants import SYMBOLS


def generate_raw_tm_tables(
    num_states: int,
    num_symbols: int = 2
) -> Generator[Dict[Tuple[int, str], Tuple[int, str, int]], None, None]:
    """
    Generate all possible Turing machine transition tables for given num_states and num_symbols.
    Uses integer enumeration and int_to_tm_table for decoding.

    :param num_states: Number of non-halting states (states 1..num_states).
    :param num_symbols: Number of tape symbols (must match configured SYMBOLS length).
    :yield: A transition table dict mapping (state, symbol) to (next_state, write_symbol, move_code).
    """
    # Ensure supported symbol count
    if num_symbols != len(SYMBOLS):
        raise ValueError(f"Only {len(SYMBOLS)} symbols supported, got num_symbols={num_symbols}")
    base = 4 * num_states + 2
    total_entries = num_states * num_symbols
    max_number = pow(base, total_entries)
    for code in range(max_number):
        # Decode the integer to a transition table
        tm_table = int_to_tm_table(code, num_states)
        yield tm_table 

def generate_reduced_tm_tables(
    num_states: int,
    num_symbols: int = 2
) -> Generator[Dict[Tuple[int, str], Tuple[int, str, int]], None, None]:
    """
    Generate a reduced set of Turing machine transition tables by symmetry:
    only machines whose initial transition (state 1 reading the blank symbol)
    moves right to a non-initial (state>1), non-halting state.

    Total machines: 2*(num_states-1)*(base^(2*num_states-1)), where base=4*num_states+2.
    """
    # Ensure supported symbol count
    if num_symbols != len(SYMBOLS):
        raise ValueError(f"Only {len(SYMBOLS)} symbols supported, got num_symbols={num_symbols}")
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