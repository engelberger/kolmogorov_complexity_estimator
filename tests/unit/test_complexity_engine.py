import pytest
import json
import math
from pathlib import Path
from kolmogorov_complexity_estimator.complexity_engine import KolmogorovComplexityEstimator


def test_estimate_K_from_dict():
    # Provide distribution directly as dict
    D = {'0': 0.5, '1': 0.125, '00': 0.0}
    estimator = KolmogorovComplexityEstimator(D)
    # K(0) = -log2(0.5) = 1
    assert pytest.approx(estimator.estimate_K('0'), rel=1e-9) == 1.0
    # K(1) = -log2(0.125) = 3
    assert pytest.approx(estimator.estimate_K('1'), rel=1e-9) == 3.0
    # Zero probability yields infinity
    assert math.isinf(estimator.estimate_K('00'))
    # Unknown string yields infinity
    assert math.isinf(estimator.estimate_K('unknown'))


def test_estimate_K_from_json_file(tmp_path):
    # Create a JSON file with D_distribution
    dist = {'D_distribution': {'10': 0.25, '11': 0.75}}
    file_path = tmp_path / 'dist.json'
    file_path.write_text(json.dumps(dist))
    estimator = KolmogorovComplexityEstimator(str(file_path))
    # K(10) = -log2(0.25) = 2
    assert pytest.approx(estimator.estimate_K('10'), rel=1e-9) == 2.0
    # K(11) = -log2(0.75) approx 0.415
    assert pytest.approx(estimator.estimate_K('11'), rel=1e-9) == -math.log2(0.75)


def test_get_ranked_strings():
    # Simple distribution
    D = {'a': 0.2, 'b': 0.5, 'c': 0.3}
    estimator = KolmogorovComplexityEstimator(D)
    ranked = estimator.get_ranked_strings()
    # b has highest probability => lowest K
    assert ranked[0][0] == 'b'
    # K order: b, c, a
    assert [s for s, k in ranked] == ['b', 'c', 'a']
    # top_n parameter
    top2 = estimator.get_ranked_strings(top_n=2)
    assert len(top2) == 2 