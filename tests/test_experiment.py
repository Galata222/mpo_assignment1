from pathlib import Path

import pandas as pd
import pytest

from cosp.run_experiment import budgeted_algorithms, expand_algorithms, thin_trace, time_limit_of

REFERENCE = Path(__file__).resolve().parent.parent / "reference" / "paper_rpd.csv"


def test_time_limit_matches_the_paper():
    assert time_limit_of(3, 2, 2, 0.12) == pytest.approx(0.72)  # smallest instances
    assert time_limit_of(50, 10, 6, 0.12) == pytest.approx(180.0)  # largest instances
    assert time_limit_of(3, 2, 2, None) is None


def test_grid_expands_to_one_variant_per_combination():
    config = {"algorithms": {
        "SA": {"type": "sa", "params": {"init": "neh"}, "grid": {"p0": [0.1, 0.3], "t_ratio": [0.01, 0.001]}},
        "IGA-String": {"type": "iga_string"},
    }}
    variants = expand_algorithms(config)
    assert len(variants) == 5
    assert ("SA[p0=0.1, t_ratio=0.01]", "sa", {"init": "neh", "p0": 0.1, "t_ratio": 0.01}) in variants
    assert ("IGA-String", "iga_string", {}) in variants


def test_algorithm_budget_replaces_the_experiment_budget():
    config = {
        "budget": {"max_full_evals": 1000},
        "algorithms": {
            "SA": {"type": "sa"},
            "SA long": {"type": "sa", "budget": {"max_full_evals": 4000}},
            "IGA timed": {"type": "iga_string", "budget": {"time_factor": 0.12}},
        },
    }
    assert budgeted_algorithms(config) == [
        ("SA", "sa", {}, None, 1000),
        ("SA long", "sa", {}, None, 4000),
        ("IGA timed", "iga_string", {}, 0.12, None),
    ]


def test_missing_budget_is_rejected():
    with pytest.raises(ValueError):
        budgeted_algorithms({"algorithms": {"SA": {"type": "sa"}}})


def test_unknown_algorithm_type_is_rejected():
    with pytest.raises(ValueError):
        expand_algorithms({"algorithms": {"X": {"type": "tabu"}}})


def test_thin_trace_keeps_the_final_value():
    trace = [(float(i), i / 1000.0, 10_000 - i) for i in range(1000)]
    thinned = thin_trace(trace, time_limit=1.0, max_full_evals=None)
    assert len(thinned) <= 201
    assert thinned[-1] == trace[-1]


def test_reference_table_matches_the_totals_printed_in_the_paper():
    """Column means must equal the 'Total' rows of Tables 9 and 10 (guards against typos)."""
    table = pd.read_csv(REFERENCE)
    totals = {
        "small": {"IGA-String": 0.0575, "IGA-Matrix1": 1.0649, "IGA-Matrix2": 0.9459, "IGA-Matrix3": 0.8983},
        "big": {"IGA-String": 0.8165, "IGA-Matrix1": 0.4443, "IGA-Matrix2": 0.3633, "IGA-Matrix3": 0.3170},
    }
    for testbed, expected in totals.items():
        rows = table[table["testbed"] == testbed]
        assert len(rows) == 27
        for column, total in expected.items():
            assert rows[column].mean() == pytest.approx(total, abs=1.1e-4)
