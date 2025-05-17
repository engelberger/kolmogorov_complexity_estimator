import pytest

from kolmogorov_complexity_estimator.complexity_engine import (
    KolmogorovComplexityEstimator,
)
from kolmogorov_complexity_estimator.output_aggregator import (
    OutputFrequencyDistribution,
)
from kolmogorov_complexity_estimator.reduction_filters import (
    check_for_cycle_two,
    check_for_escapee,
    has_no_halt_transition,
)
from kolmogorov_complexity_estimator.tm_enumerator import generate_raw_tm_tables
from kolmogorov_complexity_estimator.turing_machine import TuringMachine


@pytest.mark.parametrize("n", [1, 2])
def test_simulation_pipeline_raw_sums_to_one_and_rank(n):
    """
    End-to-end pipeline for small n with raw enumeration, verifying distribution
    sums to 1 and K ranking.
    """
    agg = OutputFrequencyDistribution(num_states=n)
    enumerator = generate_raw_tm_tables(num_states=n)
    runtime_filters = [check_for_escapee, check_for_cycle_two]
    for tm_table in enumerator:
        if has_no_halt_transition(tm_table):
            agg.record_run_outcome("filtered", None, "no_halt_transition")
        else:
            tm = TuringMachine(n, tm_table, blank_symbol="0")
            status, output, filter_name = tm.run(
                max_steps=10, runtime_filters=runtime_filters
            )
            agg.record_run_outcome(status, output, filter_name)
    # Calculate distribution
    agg.calculate_D_distribution()
    # Distribution probabilities sum to 1
    total_prob = sum(agg.D_distribution.values())
    assert pytest.approx(total_prob, rel=1e-6) == 1.0
    # Must contain keys '' (empty output) and '1'
    assert "" in agg.D_distribution and "1" in agg.D_distribution
    # Test K ranking; lowest K first
    estimator = KolmogorovComplexityEstimator(agg.D_distribution)
    ranked = estimator.get_ranked_strings()
    # Simple check: first complexity <= last complexity
    assert ranked[0][1] <= ranked[-1][1]
