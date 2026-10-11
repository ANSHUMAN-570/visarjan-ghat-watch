import numpy as np
import pytest

from src.data_loader import load_dataset
from src.metrics import benchmark_result, guide_check, overview, parameter_summary, with_benchmark

from .fixtures import CFG, canonical, site_rows


@pytest.mark.parametrize("param,value,expected", [
    ("Dissolved oxygen", 4.99, "beyond"), ("Dissolved oxygen", 5.0, "within"), ("Dissolved oxygen", 0.0, "beyond"),
    ("BOD", 3.0, "within"), ("BOD", 3.01, "beyond"),
    ("pH", 6.49, "beyond"), ("pH", 6.5, "within"), ("pH", 8.5, "within"), ("pH", 8.51, "beyond"),
])
def test_benchmark_boundaries(param, value, expected):
    assert benchmark_result(param, value, CFG) == expected


def test_nan_and_unbenchmarked_parameters_are_not_scored():
    assert benchmark_result("BOD", float("nan"), CFG) == "not_scored"
    assert benchmark_result("Lead", 0.5, CFG) == "not_scored"


def test_missing_bdl_nd_never_become_scored_values():
    df = canonical(site_rows("SYNTHETIC A", do=["4", "BDL", "ND", "not sampled", "", "7"], bod=["2"], ph=["7"]))
    b = with_benchmark(df, CFG)
    do = b[b["parameter"] == "Dissolved oxygen"]
    assert sorted(do["benchmark"]) == ["beyond", "not_scored", "not_scored", "not_scored", "not_scored", "within"]
    assert do["value"].isna().sum() == 4  # nothing was filled with 0 or an average


def test_parameter_summary_counts_and_rates():
    df = canonical(site_rows("SYNTHETIC A", do=["4", "6", "3", "BDL"], bod=["5", "5", "2"], ph=["7"]))
    s = parameter_summary(df, CFG).set_index("parameter")
    assert (s.loc["Dissolved oxygen", "n_rows"], s.loc["Dissolved oxygen", "n_valid"], s.loc["Dissolved oxygen", "n_beyond"]) == (4, 3, 2)
    assert s.loc["Dissolved oxygen", "violation_rate"] == pytest.approx(2 / 3)
    assert s.loc["Dissolved oxygen", "n_not_scored"] == 1 and s.loc["Dissolved oxygen", "completeness"] == pytest.approx(0.75)
    assert s.loc["BOD", "violation_rate"] == pytest.approx(2 / 3)
    assert s.loc["pH", "violation_rate"] == 0 and s.loc["pH", "years"] == [2025]


def test_rate_is_nan_not_zero_when_nothing_is_valid():
    df = canonical(site_rows("SYNTHETIC A", do=["BDL", "ND"], bod=["2"], ph=["7"]))
    s = parameter_summary(df, CFG).set_index("parameter")
    assert np.isnan(s.loc["Dissolved oxygen", "violation_rate"]) and s.loc["Dissolved oxygen", "n_valid"] == 0


def test_overview_matches_manual_counts():
    df = canonical(site_rows("SYNTHETIC A", do=["4", "6"], bod=["5", ""], ph=["9", "7"]) +
                   site_rows("SYNTHETIC B", do=["1"], bod=["1"], ph=["7"]))
    o = overview(df, CFG)
    assert o["n_sites"] == 2 and o["n_rows"] == len(df)
    assert (o["per_param"]["Dissolved oxygen"]["n_beyond"], o["per_param"]["Dissolved oxygen"]["n_valid"]) == (2, 3)
    assert (o["per_param"]["BOD"]["n_beyond"], o["per_param"]["BOD"]["n_valid"]) == (1, 2)
    assert (o["per_param"]["pH"]["n_beyond"], o["per_param"]["pH"]["n_valid"]) == (1, 3)
    assert o["n_unscorable_key"] == 1


def test_real_data_recalculation_matches_the_guide_reported_figures():
    df, _, cfg = load_dataset()
    g = guide_check(df, cfg)
    assert g["matches"].all(), g.to_string()
    o = overview(df, cfg)
    assert (o["per_param"]["Dissolved oxygen"]["n_beyond"], o["per_param"]["Dissolved oxygen"]["n_valid"]) == (42, 116)
    assert (o["per_param"]["BOD"]["n_beyond"], o["per_param"]["BOD"]["n_valid"]) == (100, 112)
