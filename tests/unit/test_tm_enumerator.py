import pytest
from kolmogorov_complexity_estimator.tm_enumerator import generate_raw_tm_tables, generate_reduced_tm_tables
from kolmogorov_complexity_estimator.tm_constants import SYMBOLS


def test_generate_raw_tm_tables_n1_count_and_keys():
    # For n=1, base=4*1+2=6, entries=1*2=2, so total=6^2=36
    tables = list(generate_raw_tm_tables(num_states=1))
    assert len(tables) == (4 * 1 + 2) ** (1 * len(SYMBOLS))
    # Each table must have exactly entries for state 1 and each symbol
    expected_keys = {(1, sym) for sym in SYMBOLS}
    for tm in tables:
        assert set(tm.keys()) == expected_keys
        for (state, sym), (next_state, write_symbol, move_code) in tm.items():
            assert state == 1
            assert sym in SYMBOLS
            assert isinstance(next_state, int)
            assert write_symbol in SYMBOLS
            assert isinstance(move_code, int)


def test_generate_reduced_tm_tables_n1_empty():
    # For n=1, reduced enumeration yields no machines
    tables = list(generate_reduced_tm_tables(num_states=1))
    assert tables == []


def test_generate_reduced_tm_tables_n2_count_and_keys():
    # For n=2, base=4*2+2=10, total entries=2*2=4, reduced count=2*(n-1)*(base^(2n-1))=2*1*10^3=2000
    expected_count = 2 * (2 - 1) * (10 ** (2 * 2 - 1))
    tables = list(generate_reduced_tm_tables(num_states=2))
    assert len(tables) == expected_count
    # Each table must have entries for states 1 and 2, each symbol
    expected_keys = {(s, sym) for s in (1, 2) for sym in SYMBOLS}
    for tm in tables[:10]:  # sample first 10 tables for key structure
        assert set(tm.keys()) == expected_keys

# End of test_tm_enumerator.py 