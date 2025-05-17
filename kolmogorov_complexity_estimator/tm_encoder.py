# Logic for TM encoding/decoding to/from integers 
from typing import Dict, Tuple
from .tm_constants import SYMBOLS, HALT_STATE, MOVES

# Invert MOVES mapping for decoding
CODE_TO_MOVE_CHAR = {code: char for char, code in MOVES.items()}


def tm_to_int(
    tm_table: Dict[Tuple[int, str], Tuple[int, str, int]],
    n_states: int
) -> int:
    """
    Encode a full Turing machine transition table as an integer in [0, (4n+2)^(2n) - 1].
    The table must contain exactly entries for states 1..n and symbols in SYMBOLS.
    """
    base = 4 * n_states + 2
    # Verify expected keys
    expected_keys = [(s, sym) for s in range(1, n_states + 1) for sym in SYMBOLS]
    for key in expected_keys:
        if key not in tm_table:
            raise ValueError(f"Missing transition for state,symbol {key}")
    # Build digits (big-endian)
    digits = []
    for state in range(1, n_states + 1):
        for sym in SYMBOLS:
            next_state, write_symbol, move_code = tm_table[(state, sym)]
            # HALT_STATE entries
            if next_state == HALT_STATE:
                # move must be N
                if move_code != MOVES['N']:
                    raise ValueError(f"Invalid move for HALT_STATE: {move_code}")
                # write_symbol index gives code 0 or 1
                if write_symbol not in SYMBOLS:
                    raise ValueError(f"Invalid write symbol: {write_symbol}")
                code = SYMBOLS.index(write_symbol)
            else:
                # Active state entries
                if not (1 <= next_state <= n_states):
                    raise ValueError(f"Invalid next_state {next_state} for key {(state, sym)}")
                if write_symbol not in SYMBOLS:
                    raise ValueError(f"Invalid write symbol: {write_symbol}")
                # Determine move_char index
                if move_code == MOVES['L']:
                    move_idx = 0
                elif move_code == MOVES['R']:
                    move_idx = 1
                else:
                    raise ValueError(f"Invalid move code for non-halt state: {move_code}")
                write_idx = SYMBOLS.index(write_symbol)
                # Compute code offset: 2 + 4*(state-1) + write_idx*2 + move_idx
                code = 2 + (next_state - 1) * (len(SYMBOLS) * 2) + (write_idx * 2 + move_idx)
            digits.append(code)
    # Combine digits into integer
    number = 0
    for d in digits:
        if not (0 <= d < base):
            raise ValueError(f"Digit {d} out of range for base {base}")
        number = number * base + d
    return number


def int_to_tm_table(
    number: int,
    n_states: int
) -> Dict[Tuple[int, str], Tuple[int, str, int]]:
    """
    Decode an integer in [0, (4n+2)^(2n) - 1] back into a transition table mapping.
    Returns a dict: (state, read_symbol) -> (next_state, write_symbol, move_code).
    """
    base = 4 * n_states + 2
    total_entries = 2 * n_states
    max_number = pow(base, total_entries)
    if not (0 <= number < max_number):
        raise ValueError(f"Number out of valid range 0..{max_number-1}, got {number}")
    # Extract digits (big-endian)
    digits = []
    remainder = number
    # Precompute powers
    powers = [pow(base, total_entries - i - 1) for i in range(total_entries)]
    for power in powers:
        d = remainder // power
        digits.append(d)
        remainder -= d * power
    # Reconstruct table
    tm_table: Dict[Tuple[int, str], Tuple[int, str, int]] = {}
    idx = 0
    for state in range(1, n_states + 1):
        for sym in SYMBOLS:
            code = digits[idx]
            idx += 1
            if code < 2:
                # HALT_STATE entry
                next_state = HALT_STATE
                write_symbol = SYMBOLS[code]
                move_code = MOVES['N']
            else:
                # Active state entry
                offset = code - 2
                combos = len(SYMBOLS) * 2
                state_idx = offset // combos
                inner = offset % combos
                write_idx = inner // 2
                move_idx = inner % 2
                next_state = state_idx + 1
                write_symbol = SYMBOLS[write_idx]
                # Determine move_char and code
                move_char = ['L', 'R'][move_idx]
                move_code = MOVES[move_char]
            tm_table[(state, sym)] = (next_state, write_symbol, move_code)
    return tm_table 