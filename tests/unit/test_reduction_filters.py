from collections import defaultdict

from kolmogorov_complexity_estimator.reduction_filters import (
    check_for_cycle_two,
    check_for_escapee,
    has_no_halt_transition,
)
from kolmogorov_complexity_estimator.tm_constants import HALT_STATE


class DummyTM:
    def __init__(self, num_states, sequence=None):
        self.num_states = num_states
        self.head_position = 0
        self.blank_symbol = "0"
        self.tape = defaultdict(lambda: "0")
        self._escapee_seen_positions = set()
        self._escapee_blank_run_count = 0
        self._cycle_history = None
        # Optional: initial sequence of (state, pos, tape)
        self.current_state = 1


def test_has_no_halt_transition_true():
    tm_table = {(1, "0"): (1, "0", 1), (1, "1"): (1, "1", -1)}
    assert has_no_halt_transition(tm_table) is True


def test_has_no_halt_transition_false():
    tm_table = {(1, "0"): (HALT_STATE, "0", 0)}
    assert has_no_halt_transition(tm_table) is False


def test_check_for_escapee_triggers_after_n_plus_one_blank_moves():
    tm = DummyTM(num_states=3)
    # Move to fresh blank cells sequentially
    results = []
    for i in range(5):  # > num_states
        tm.head_position = i
        # tape is blank by default
        results.append(check_for_escapee(tm))
    # Should be False for first num_states moves, True afterwards
    assert results[:3] == [False, False, False]
    assert all(results[3:])


def test_check_for_cycle_two_triggers_on_repetition():
    tm = DummyTM(num_states=2)
    # Initialize cycle history
    tm._cycle_history = None
    outputs = []
    for _ in range(3):
        # Keep state and head fixed, tape unchanged
        outputs.append(check_for_cycle_two(tm))
    # Third call should detect cycle (config0 == config2)
    assert outputs == [False, False, True]


# End of test_reduction_filters.py
