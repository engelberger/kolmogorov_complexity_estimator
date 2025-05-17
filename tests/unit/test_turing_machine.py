# Unit tests for TuringMachine
from kolmogorov_complexity_estimator.reduction_filters import (
    check_for_cycle_two,
    check_for_escapee,
)
from kolmogorov_complexity_estimator.turing_machine import TuringMachine


def test_halt_writes_and_output():
    # TM that writes '1' and halts immediately
    table = {(1, "0"): (0, "1", 0)}
    tm = TuringMachine(1, table)
    status, output, filter_name = tm.run(max_steps=1)
    assert status == "halted"
    assert output == "1"
    assert filter_name is None


def test_timeout_when_max_steps_zero():
    # TM that would halt but max_steps is zero
    table = {(1, "0"): (0, "1", 0)}
    tm = TuringMachine(1, table)
    status, output, filter_name = tm.run(max_steps=0)
    assert status == "timeout"
    assert output is None
    assert filter_name is None


def test_missing_transition_halts_with_empty_output():
    # TM with no transitions should immediately halt with no output
    table = {}
    tm = TuringMachine(1, table)
    status, output, _ = tm.run(max_steps=1)
    assert status == "halted"
    assert output == ""


def test_escapee_filter_triggers():
    # TM that moves right on blank repeatedly -> escapee
    table = {(1, "0"): (1, "0", 1)}
    tm = TuringMachine(1, table)
    status, output, filter_name = tm.run(
        max_steps=10, runtime_filters=[check_for_escapee]
    )
    assert status == "filtered"
    assert output is None
    assert filter_name == "check_escapee"


def test_cycle_two_filter_triggers():
    # TM that oscillates between two states and positions -> cycle of period two
    table = {(1, "0"): (2, "0", 1), (2, "0"): (1, "0", -1)}
    tm = TuringMachine(2, table)
    status, output, filter_name = tm.run(
        max_steps=10, runtime_filters=[check_for_cycle_two]
    )
    assert status == "filtered"
    assert output is None
    assert filter_name == "check_cycle_two"


# End of test_turing_machine.py
