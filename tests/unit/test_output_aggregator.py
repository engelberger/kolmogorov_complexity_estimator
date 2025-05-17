import pytest
import json
from collections import Counter
from pathlib import Path
tmp_path = Path
from kolmogorov_complexity_estimator.output_aggregator import OutputFrequencyDistribution


def test_record_run_outcome():
    agg = OutputFrequencyDistribution(num_states=2)
    agg.record_run_outcome('halted', '00', None)
    agg.record_run_outcome('timeout', None, None)
    agg.record_run_outcome('filtered', None, 'escape')
    assert agg.total_processed_raw == 3
    assert agg.total_halting_raw == 1
    assert agg.output_counts['00'] == 1
    assert agg.non_halting_reasons['timeout'] == 1
    assert agg.non_halting_reasons['escape'] == 1


def test_apply_completion_and_D_distribution():
    agg = OutputFrequencyDistribution(num_states=2)
    # Setup raw data: one halted output '0', no non-halting
    agg.output_counts = Counter({'0': 1})
    agg.non_halting_reasons = Counter()
    # Apply completion for reduced set M_red=4
    agg.apply_completion_rules(M_red=4)
    # Effective counts: per logic: '0':6, '1':6
    assert agg.effective_output_counts['0'] == 6
    assert agg.effective_output_counts['1'] == 6
    assert agg.effective_halting == 12
    assert agg.effective_non_halting == 16
    assert agg.effective_total == 28
    # Calculate D distribution
    agg.calculate_D_distribution()
    assert pytest.approx(agg.D_distribution['0'], rel=1e-6) == 0.5
    assert pytest.approx(agg.D_distribution['1'], rel=1e-6) == 0.5


def test_save_load_distribution(tmp_path):
    agg = OutputFrequencyDistribution(num_states=2)
    agg.record_run_outcome('halted', '01', None)
    agg.record_run_outcome('filtered', None, 'escape')
    # Calculate raw distribution
    agg.calculate_D_distribution()
    out_file = tmp_path / 'dist.json'
    agg.save_distribution_to_file(str(out_file), raw=True)
    # Load into new aggregator
    agg2 = OutputFrequencyDistribution(num_states=2)
    agg2.load_distribution_from_file(str(out_file), raw=True)
    assert agg2.num_states == agg.num_states
    assert agg2.total_processed_raw == agg.total_processed_raw
    assert agg2.total_halting_raw == agg.total_halting_raw
    assert agg2.output_counts == agg.output_counts
    assert agg2.non_halting_reasons == agg.non_halting_reasons
    # Raw did not save D_distribution, so new aggregator's D_distribution should be empty
    assert agg2.D_distribution == {} 