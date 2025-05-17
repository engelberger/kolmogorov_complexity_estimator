# TuringMachine class, simulation logic 
from collections import defaultdict
from typing import Dict, Tuple, List, Callable, Optional
from .tm_constants import BLANK_SYMBOL_DEFAULT, HALT_STATE


class TuringMachine:
    """
    Turing Machine simulator using a finite-state transition table.

    States are integers 1..n, with a dedicated HALT_STATE (0).
    The machine runs on an infinite tape initialized with a blank symbol.
    """

    def __init__(
        self,
        num_states: int,
        transition_table: Dict[Tuple[int, str], Tuple[int, str, int]],
        blank_symbol: str = BLANK_SYMBOL_DEFAULT,
    ):
        """
        Initialize the Turing machine.

        :param num_states: Number of non-halting states (states 1..num_states).
        :param transition_table: Mapping from (current_state, read_symbol) to
                                 (next_state, write_symbol, move_code).
        :param blank_symbol: Symbol representing blank on the tape.
        """
        self.num_states = num_states
        self.transition_table = transition_table
        self.blank_symbol = blank_symbol
        # Tape represented as a defaultdict for infinite tape
        self.tape = defaultdict(lambda: blank_symbol)
        self.head_position = 0
        self.current_state = 1  # Start state
        self.steps_taken = 0
        # Track range of head positions visited (useful for filters)
        self.min_visited = 0
        self.max_visited = 0

    def step(self) -> bool:
        """
        Perform one step of the Turing machine.

        :return: True if machine should continue, False if it has halted.
        """
        # If already in halt state, stop
        if self.current_state == HALT_STATE:
            return False
        # Read current symbol
        symbol = self.tape[self.head_position]
        key = (self.current_state, symbol)
        # If no transition defined, treat as halt
        if key not in self.transition_table:
            self.current_state = HALT_STATE
            return False
        # Apply transition
        next_state, write_symbol, move_code = self.transition_table[key]
        # Write to tape
        self.tape[self.head_position] = write_symbol
        # Update state
        self.current_state = next_state
        # Move head
        self.head_position += move_code
        # Update visited range
        self.min_visited = min(self.min_visited, self.head_position)
        self.max_visited = max(self.max_visited, self.head_position)
        # Increment step counter
        self.steps_taken += 1
        # If transition moved to halt state, halt after writing
        if self.current_state == HALT_STATE:
            return False
        return True

    def run(
        self,
        max_steps: int,
        runtime_filters: Optional[List[Callable[['TuringMachine'], bool]]] = None,
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Run the Turing machine up to a maximum number of steps.

        :param max_steps: Maximum number of steps to execute.
        :param runtime_filters: Optional list of filter functions that accept this
                                machine and return True to signal early stopping.
        :return: A tuple (status, output_string, filter_name).
                 status is 'halted', 'timeout', or 'filtered'.
                 output_string is defined if halted, else None.
                 filter_name is the __name__ of the filter that triggered stopping, if any.
        """
        filters = runtime_filters or []
        while self.steps_taken < max_steps:
            # Execute one step
            continue_run = self.step()
            if not continue_run:
                # Machine halted
                output = self._extract_output_string()
                return 'halted', output, None
            # Apply runtime filters after step
            for f in filters:
                if f(self):
                    return 'filtered', None, f.__name__
        # Reached max steps without halting or filtering
        return 'timeout', None, None

    def _extract_output_string(self) -> str:
        """
        Extract the output string from the tape, defined as the contents
        from the leftmost to the rightmost non-blank symbol.

        :return: The output binary string, or empty string if no non-blank symbols.
        """
        # Find positions with non-blank symbols
        non_blank_positions = [pos for pos, sym in self.tape.items() if sym != self.blank_symbol]
        if not non_blank_positions:
            return ''
        left = min(non_blank_positions)
        right = max(non_blank_positions)
        # Collect symbols in range
        return ''.join(self.tape[pos] for pos in range(left, right + 1)) 