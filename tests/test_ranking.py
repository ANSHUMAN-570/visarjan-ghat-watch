import numpy as np
import pandas as pd
import pytest

from src.data_loader import load_dataset
from src.ranking import INSUFFICIENT, SCORED, rank_sites

from .fixtures import CFG, canonical, site_rows


def test_score_formula_uses_configured_weights():
    # DO 2/4 beyond, BOD 4/4, pH 0/4  ->  100 * (0.4*0.5 + 0.4*1.0 + 0.2*0)
    df = canonical(site_rows("SYNTHETIC A", do=["4", "4", "6", "7"], bod=["5"] * 4, ph=["7"] * 4))
    r = rank_sites(df, CFG).iloc[0]
    assert r["score"] == pytest.approx(60.0) and r["ranking_status"] == SCORED
    assert r["DO_n_valid"] == 4 and r["DO_n_beyond"] == 2 and r["BOD_rate"] == 1.0


def test_missing_parameter_is_dropped_and_weights_renormalised_not_zeroed():
    # pH has no valid reading: weights become DO 0.5 / BOD 0.5 -> 100 * (0.5*0.5 + 0.5*1.0) = 75, NOT 60
    df = canonical(site_rows("SYNTHETIC A", do=["4", "4", "6", "7"], bod=["5"] * 4, ph=["BDL", "ND", "", "not sampled"]))
    r = rank_sites(df, CFG).iloc[0]
    assert r["score"] == pytest.approx(75.0)
    assert r["params_without_data"] == ["pH"]
    assert r["weights_used"] == {"Dissolved oxygen": pytest.approx(0.5), "BOD": pytest.approx(0.5)}


def test_site_with_no_usable_readings_is_insufficient_not_zero_or_safe():
    rows = site_rows("SYNTHETIC GOOD", do=["7"] * 3, bod=["1"] * 3, ph=["7"] * 3) + \
        site_rows("SYNTHETIC EMPTY", do=["", "BDL", "not sampled"], bod=["", "ND", ""], ph=["", "", "*"])
    r = rank_sites(canonical(rows), CFG).set_index("site")
    assert r.loc["SYNTHETIC EMPTY", "ranking_status"] == INSUFFICIENT
    assert np.isnan(r.loc["SYNTHETIC EMPTY", "score"]) and pd.isna(r.loc["SYNTHETIC EMPTY", "rank"])
    assert r.loc["SYNTHETIC GOOD", "score"] == 0.0  # a genuinely clean site scores 0; an unknown one does not


def test_site_requested_but_absent_from_data_is_insufficient():
    df = canonical(site_rows("SYNTHETIC A", do=["4"], bod=["5"], ph=["7"]))
    r = rank_sites(df, CFG, sites=["SYNTHETIC A", "SYNTHETIC NEVER TESTED"]).set_index("site")
    assert r.loc["SYNTHETIC NEVER TESTED", "ranking_status"] == INSUFFICIENT


def test_insufficient_sites_sort_last_and_scored_sites_by_score():
    rows = (site_rows("SYNTHETIC LOW", do=["7"] * 3, bod=["1"] * 3, ph=["7"] * 3)
            + site_rows("SYNTHETIC HIGH", do=["1"] * 3, bod=["9"] * 3, ph=["7"] * 3)
            + site_rows("SYNTHETIC ZZZ EMPTY", do=[""] * 3, bod=[""] * 3, ph=[""] * 3))
    r = rank_sites(canonical(rows), CFG)
    assert list(r["site"]) == ["SYNTHETIC HIGH", "SYNTHETIC LOW", "SYNTHETIC ZZZ EMPTY"]
    assert list(r["rank"].dropna()) == [1, 2]


def test_ranking_is_deterministic_and_ties_break_by_name():
    rows = (site_rows("SYNTHETIC B", do=["4"] * 3, bod=["5"] * 3, ph=["7"] * 3)
            + site_rows("SYNTHETIC A", do=["4"] * 3, bod=["5"] * 3, ph=["7"] * 3))
    df = canonical(rows)
    first = rank_sites(df, CFG)
    shuffled = rank_sites(df.sample(frac=1, random_state=7).reset_index(drop=True), CFG)
    assert list(first["site"]) == list(shuffled["site"]) == ["SYNTHETIC A", "SYNTHETIC B"]
    pd.testing.assert_series_equal(first["score"], shuffled["score"])


def test_low_sample_is_flagged_next_to_the_score():
    df = canonical(site_rows("SYNTHETIC A", do=["4"], bod=["5", "5", "5"], ph=["7", "7", "7"]))
    r = rank_sites(df, CFG).iloc[0]
    assert r["low_sample"] and r["DO_n_valid"] == 1


def test_min_valid_readings_setting_is_respected():
    cfg = {**CFG, "scoring": {**CFG["scoring"], "min_valid_readings_per_site": 10}}
    df = canonical(site_rows("SYNTHETIC A", do=["4"] * 3, bod=["5"] * 3, ph=["7"] * 3))
    assert rank_sites(df, cfg).iloc[0]["ranking_status"] == INSUFFICIENT


def test_real_data_ranking_is_stable_and_complete():
    df, _, cfg = load_dataset()
    a, b = rank_sites(df, cfg), rank_sites(df.iloc[::-1].reset_index(drop=True), cfg)
    assert list(a["site"]) == list(b["site"]) and len(a) == 7
    assert a.iloc[0]["site"].startswith("Bairagarh")
    assert (a["ranking_status"] == SCORED).all() and a["score"].between(0, 100).all()
    # counts behind the ranking agree with the overview
    assert a["DO_n_valid"].sum() == 116 and a["DO_n_beyond"].sum() == 42
    assert a["BOD_n_valid"].sum() == 112 and a["BOD_n_beyond"].sum() == 100
