# Parsing TM transition table strings/definitions 
from typing import List, Tuple, Dict
from .tm_constants import SYMBOLS, MOVES


def parse_transition_table(
    transitions: List[Tuple[int, str, int, str, str]]
) -> Dict[Tuple[int, str], Tuple[int, str, int]]:
    """
    Parse a Turing machine transition list into a mapping from (current_state, read_symbol)
    to (next_state, write_symbol, move_code).
    Each transition is a 5-tuple: (current_state, read_symbol, next_state, write_symbol, move_char).
    move_char must be one of MOVES keys: 'L', 'R', 'N'.
    """
    table: Dict[Tuple[int, str], Tuple[int, str, int]] = {}
    for entry in transitions:
        if not isinstance(entry, (tuple, list)) or len(entry) != 5:
            raise ValueError(
                f"Transition {entry} is not a 5-tuple (current_state, read_symbol, next_state, write_symbol, move_char)"
            )
        current_state, read_symbol, next_state, write_symbol, move_char = entry
        # Type validations
        if not isinstance(current_state, int):
            raise TypeError(f"Current state must be int, got {type(current_state).__name__}: {current_state}")
        if not isinstance(next_state, int):
            raise TypeError(f"Next state must be int, got {type(next_state).__name__}: {next_state}")
        # Symbol validations
        if read_symbol not in SYMBOLS:
            raise ValueError(f"Read symbol must be one of {SYMBOLS}, got: {read_symbol}")
        if write_symbol not in SYMBOLS:
            raise ValueError(f"Write symbol must be one of {SYMBOLS}, got: {write_symbol}")
        # Move validations
        if move_char not in MOVES:
            raise ValueError(f"Move character must be one of {list(MOVES.keys())}, got: {move_char}")
        key = (current_state, read_symbol)
        if key in table:
            raise ValueError(f"Duplicate transition for state {current_state} and symbol {read_symbol}")
        move_code = MOVES[move_char]
        table[key] = (next_state, write_symbol, move_code)
    return table 