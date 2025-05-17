# Logic for TM encoding/decoding to/from integers
from typing import Dict, Tuple

from .tm_constants import HALT_STATE, MOVES, SYMBOLS

# Attempt to import native Cython implementations
try:
    from .native.encoder import int_to_tm_table as native_int_to_tm_table
    from .native.encoder import tm_to_int as native_tm_to_int

    _USE_NATIVE = True
except ImportError:
    # print(
    #     "Warning: Cython-optimized TM encoder/decoder not found. "
    #     "Using Python fallback."
    # )
    _USE_NATIVE = False

    # Define stubs if native isn't found so the functions still exist
    def native_tm_to_int(
        tm_table: Dict[Tuple[int, str], Tuple[int, str, int]], n_states: int
    ) -> int:
        raise NotImplementedError(
            "Native tm_to_int not available and Python version removed to enforce"
            " native usage."
        )

    def native_int_to_tm_table(
        number: int, n_states: int
    ) -> Dict[Tuple[int, str], Tuple[int, str, int]]:
        raise NotImplementedError(
            "Native int_to_tm_table not available and Python version removed to"
            " enforce native usage."
        )


# Invert MOVES mapping for decoding - still needed for Python version
# of int_to_tm_table if kept
# CODE_TO_MOVE_CHAR = {code: char for char, code in MOVES.items()}
# # Not strictly needed if native is always used

# Python helper _encode_transition is removed as its logic is now in
# Cython's _encode_transition_cy


def tm_to_int(  # noqa: C901
    tm_table: Dict[Tuple[int, str], Tuple[int, str, int]], n_states: int
) -> int:
    """
    Encode a full Turing machine transition table as an integer.
    Uses native Cython implementation if available.
    """
    if _USE_NATIVE:
        return native_tm_to_int(tm_table, n_states)
    else:
        # This is the pure Python fallback implementation
        base = 4 * n_states + 2
        expected_keys = [(s, sym) for s in range(1, n_states + 1) for sym in SYMBOLS]
        for key in expected_keys:
            if key not in tm_table:
                raise ValueError(f"Missing transition for state,symbol {key}")

        number = 0

        # Local helper for Python version (re-defined here as outer one is removed)
        def _py_encode_transition_local(
            next_s, write_s, move_c, n_s, curr_s_err, curr_sym_err
        ):
            if next_s == HALT_STATE:
                if move_c != MOVES["N"]:
                    raise ValueError(f"Invalid move for HALT_STATE: {move_c}")
                if write_s not in SYMBOLS:
                    raise ValueError(f"Invalid write symbol: {write_s}")
                return SYMBOLS.index(write_s)
            else:
                if not (1 <= next_s <= n_s):
                    raise ValueError(
                        f"Invalid next_state {next_s} for key "
                        f"{(curr_s_err, curr_sym_err)}"
                    )
                if write_s not in SYMBOLS:
                    raise ValueError(f"Invalid write symbol: {write_s}")
                if move_c == MOVES["L"]:
                    move_idx_local = 0
                elif move_c == MOVES["R"]:
                    move_idx_local = 1
                else:
                    raise ValueError(f"Invalid move code for non-halt state: {move_c}")
                write_idx_local = SYMBOLS.index(write_s)
                return (
                    2
                    + (next_s - 1) * (len(SYMBOLS) * 2)
                    + (write_idx_local * 2 + move_idx_local)
                )

        for state_loop in range(1, n_states + 1):
            for sym_loop in SYMBOLS:
                next_state_val, write_symbol_val, move_code_val = tm_table[
                    (state_loop, sym_loop)
                ]
                code_val = _py_encode_transition_local(
                    next_state_val,
                    write_symbol_val,
                    move_code_val,
                    n_states,
                    state_loop,
                    sym_loop,
                )
                if not (0 <= code_val < base):
                    raise ValueError(f"Digit {code_val} out of range for base {base}")
                number = number * base + code_val
        return number


def int_to_tm_table(
    number: int, n_states: int
) -> Dict[Tuple[int, str], Tuple[int, str, int]]:
    """
    Decode an integer back into a transition table mapping.
    Uses native Cython implementation if available.
    """
    if _USE_NATIVE:
        return native_int_to_tm_table(number, n_states)
    else:
        # This is the pure Python fallback implementation
        base = 4 * n_states + 2
        total_entries = 2 * n_states
        # Need to use Python's arbitrary precision for pow if numbers are large
        max_val = pow(base, total_entries)
        if not (0 <= number < max_val):
            raise ValueError(f"Number out of valid range 0..{max_val-1}, got {number}")

        digits_list = []
        remainder_val = number
        for _ in range(total_entries):
            digits_list.append(remainder_val % base)
            remainder_val //= base
        digits_list.reverse()  # To get MSB first, consistent with Cython approach

        tm_table_py: Dict[Tuple[int, str], Tuple[int, str, int]] = {}
        idx_val = 0
        for state_loop in range(1, n_states + 1):
            for sym_loop in SYMBOLS:
                code_val = digits_list[idx_val]
                idx_val += 1
                if code_val < len(SYMBOLS):  # Usually 2 for SYMBOLS = ['0', '1']
                    next_s = HALT_STATE
                    write_s = SYMBOLS[code_val]
                    move_c = MOVES["N"]
                else:
                    offset = code_val - len(SYMBOLS)
                    combos = len(SYMBOLS) * 2
                    state_idx_local = offset // combos
                    inner = offset % combos
                    write_idx_local = inner // 2
                    move_idx_local = inner % 2
                    next_s = state_idx_local + 1
                    write_s = SYMBOLS[write_idx_local]
                    move_char_local = ["L", "R"][
                        move_idx_local
                    ]  # MOVES_CHAR_LIST = ['L', 'R']
                    move_c = MOVES[move_char_local]
                tm_table_py[(state_loop, sym_loop)] = (next_s, write_s, move_c)
        return tm_table_py
