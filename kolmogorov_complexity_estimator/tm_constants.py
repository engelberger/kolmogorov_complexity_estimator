# TM alphabet, states, moves, HALT_STATE 

# Constants for the Turing machine simulator
SYMBOLS = ['0', '1']
BLANK_SYMBOL_DEFAULT = SYMBOLS[0]

# Halt state identifier
HALT_STATE = 0

# Movement codes
MOVE_LEFT = -1
MOVE_RIGHT = 1
MOVE_NONE = 0

# Map move characters to codes
MOVES = {
    'L': MOVE_LEFT,
    'R': MOVE_RIGHT,
    'N': MOVE_NONE,
} 