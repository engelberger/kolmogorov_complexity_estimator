"""
Utilities for parallel CTM simulation: initialization and per-table processing.
"""

from collections import Counter

from .reduction_filters import has_no_halt_transition
from .tm_encoder import int_to_tm_table
from .turing_machine import TuringMachine

# Globals for worker processes
_GLOBAL_N_STATES = None
_GLOBAL_BLANK_SYMBOL = None
_GLOBAL_MAX_STEPS = None
_GLOBAL_RUNTIME_FILTERS = None


def initialize_globals(n_states, blank_symbol, max_steps, runtime_filters):
    """
    Initialize global variables in worker processes for CTM simulation.
    """
    global _GLOBAL_N_STATES, _GLOBAL_BLANK_SYMBOL, _GLOBAL_MAX_STEPS
    global _GLOBAL_RUNTIME_FILTERS
    _GLOBAL_N_STATES = n_states
    _GLOBAL_BLANK_SYMBOL = blank_symbol
    _GLOBAL_MAX_STEPS = max_steps
    _GLOBAL_RUNTIME_FILTERS = runtime_filters


def process_tm(tm_table):
    """
    Worker function to process a single TM table: applies pre-run filter and
    runs the machine.
    Returns (status, output_string, filter_name).
    """
    if has_no_halt_transition(tm_table):
        return ("filtered", None, "no_halt_transition")
    tm = TuringMachine(
        num_states=_GLOBAL_N_STATES,
        transition_table=tm_table,
        blank_symbol=_GLOBAL_BLANK_SYMBOL,
    )
    return tm.run(_GLOBAL_MAX_STEPS, runtime_filters=_GLOBAL_RUNTIME_FILTERS)


def process_tm_batch(tm_numbers):
    """
    Process a batch of TM numbers. Returns aggregated results for the batch:
    (batch_output_counts, batch_non_halting_reasons, batch_total_processed,
    batch_total_halting)
    """
    batch_output_counts = Counter()
    batch_non_halting_reasons = Counter()
    batch_total_processed = 0
    batch_total_halting = 0
    for tm_number in tm_numbers:
        batch_total_processed += 1

        # Decode TM number to TM table
        # _GLOBAL_N_STATES must be initialized in the worker by initialize_globals
        tm_table = int_to_tm_table(tm_number, _GLOBAL_N_STATES)

        # Pre-run filter
        if has_no_halt_transition(tm_table):
            batch_non_halting_reasons["no_halt_transition"] += 1
            continue
        # Run TM
        tm = TuringMachine(
            num_states=_GLOBAL_N_STATES,
            transition_table=tm_table,
            blank_symbol=_GLOBAL_BLANK_SYMBOL,
        )
        status, output, filter_name = tm.run(
            _GLOBAL_MAX_STEPS, runtime_filters=_GLOBAL_RUNTIME_FILTERS
        )
        if status == "halted" and output is not None:
            batch_total_halting += 1
            batch_output_counts[output] += 1
        elif status == "timeout":
            batch_non_halting_reasons["timeout"] += 1
        elif status == "filtered" and filter_name:
            batch_non_halting_reasons[filter_name] += 1
        else:
            batch_non_halting_reasons["unknown"] += 1
    # Return lists of items instead of Counter objects to potentially reduce
    # pickling overhead
    return (
        list(batch_output_counts.items()),
        list(batch_non_halting_reasons.items()),
        batch_total_processed,
        batch_total_halting,
    )
