import pandas as pd
import pytest

from visarjan.brief import to_html, to_markdown
from visarjan.data import Limit, load_limits, load_readings
from visarjan.i18n import UI, render_reason
from visarjan.scoring import evaluate, score_ghats

R = load_readings()
L = load_limits()
DO = R[R.parameter == "Dissolved oxygen"]
BOD = R[R.parameter == "BOD"]


# ---- problem-statement facts ---------------------------------------------------------------
def test_do_counts_match_problem_statement():
    assert len(DO) == 120 and DO.value.notna().sum() == 116 and (DO.value < 5).sum() == 42


def test_bod_counts_match_problem_statement():
    assert BOD.value.notna().sum() == 112 and (BOD.value > 3).sum() == 100


def test_bairagarh_zero_oxygen_four_times():
    res = {g.site: g for g in score_ghats(R, L)}
    b = [g for s, g in res.items() if s.startswith("Bairagarh")][0]
    assert b.params["Dissolved oxygen"].n_zero == 4


def test_limits_loaded_from_cpcb_class_b():
    assert (L["Dissolved oxygen"].kind, L["Dissolved oxygen"].lo) == ("min", 5.0)
    assert (L["BOD"].kind, L["BOD"].hi) == ("max", 3.0)
    assert (L["pH"].lo, L["pH"].hi) == (6.5, 8.5)


# ---- missing-data rules --------------------------------------------------------------------
def test_status_classification():
    assert set(R.loc[R.flag == "BDL", "status"]) == {"very_low"}
    assert set(R.loc[R.flag == "not sampled", "status"]) == {"missing"}
    assert set(R.loc[R.flag.isin(["*", "**"]), "status"]) == {"missing"}


def test_missing_is_never_clean():
    assert evaluate("missing", float("nan"), L["BOD"]) == ("missing", 0.0)
    assert evaluate("missing", float("nan"), L["Dissolved oxygen"]) == ("missing", 0.0)


def test_below_detection_semantics():
    assert evaluate("very_low", float("nan"), L["BOD"])[0] == "ok"
    assert evaluate("very_low", float("nan"), L["Dissolved oxygen"])[0] == "violation"
    assert evaluate("very_low", float("nan"), L["pH"])[0] == "missing"


@pytest.mark.parametrize("param,value,state", [
    ("Dissolved oxygen", 4.9, "violation"), ("Dissolved oxygen", 5.0, "ok"), ("BOD", 3.0, "ok"),
    ("BOD", 3.1, "violation"), ("pH", 6.4, "violation"), ("pH", 8.5, "ok"), ("pH", 8.6, "violation")])
def test_limit_boundaries(param, value, state):
    assert evaluate("value", value, L[param])[0] == state


def test_severity_is_bounded():
    assert evaluate("value", 0.0, L["Dissolved oxygen"]) == ("violation", 1.0)
    assert evaluate("value", 50.0, L["BOD"])[1] == 1.0


def _synthetic(rows):
    cols = ["year", "festival", "site", "water_body", "phase", "parameter", "value", "status", "source_page"]
    df = pd.DataFrame(rows, columns=cols)
    df["phase"] = pd.Categorical(df["phase"], ["pre", "during", "after"], ordered=True)
    return df


def _full_event(site, year, fest, do, bod, ph=7.0):
    rows = []
    for phase in ("pre", "during", "after"):
        for p, v in (("Dissolved oxygen", do), ("BOD", bod), ("pH", ph)):
            rows.append([year, fest, site, "Lake", phase, p, v, "value" if v == v else "missing", 1])
    return rows


def test_missing_data_does_not_make_a_ghat_look_cleaner():
    nan = float("nan")
    clean = _full_event("Clean", 2025, "Durga", 7, 1) + _full_event("Gappy", 2025, "Durga", nan, nan, nan)
    res = {g.site: g for g in score_ghats(_synthetic(clean), L)}
    assert res["Gappy"].low_confidence and res["Gappy"].coverage == 0
    assert res["Gappy"].score == 0.0  # no evidence is not "bad"...
    assert "retest" in res["Gappy"].actions  # ...but it is never reported as clean/OK
    assert any(r["type"] == "gap_missing" for r in res["Gappy"].reasons)


def test_missing_festival_table_is_flagged():
    rows = _full_event("A", 2024, "Durga", 7, 1) + _full_event("A", 2025, "Durga", 7, 1) \
        + _full_event("B", 2024, "Durga", 7, 1)
    res = {g.site: g for g in score_ghats(_synthetic(rows), L)}
    assert res["B"].missing_events == [(2025, "Durga")] and res["B"].low_confidence
    assert not res["A"].low_confidence


def test_ranking_orders_bad_above_good():
    rows = _full_event("Good", 2025, "Durga", 7, 1) + _full_event("Bad", 2025, "Durga", 0.5, 12)
    res = score_ghats(_synthetic(rows), L)
    assert [g.site for g in res] == ["Bad", "Good"] and res[0].tier == "high" and res[1].tier == "low"
    assert [g.rank for g in res] == [1, 2]


def test_empty_selection():
    assert score_ghats(R, L, festival="Durga", years=[1999]) == []


# ---- real data sanity ----------------------------------------------------------------------
def test_all_seven_ghats_ranked_and_sorted():
    res = score_ghats(R, L)
    assert len(res) == 7
    assert [g.score for g in res] == sorted((g.score for g in res), reverse=True)
    assert res[0].site.startswith("Bairagarh")


def test_ghats_without_durga_2025_are_flagged():
    flagged = {g.site.split()[0] for g in score_ghats(R, L, festival="Durga") if g.low_confidence}
    assert {"Bairagarh", "Malikhedi"} <= flagged


# ---- brief ---------------------------------------------------------------------------------
def test_brief_contains_both_languages_and_caveats():
    res = score_ghats(R, L, festival="Durga")
    html = to_html(res, ("en", "hi"), "Durga")
    assert "विसर्जन" in html and "Ghat risk brief" in html and "not a health or safety certificate" in html
    md = to_markdown(res, "hi", "Durga")
    assert "घुलित ऑक्सीजन" in md and "Bairagarh" in md


def test_every_reason_renders_in_both_languages():
    for g in score_ghats(R, L):
        for r in g.reasons:
            for lang in UI:
                assert "{" not in render_reason(r, lang)


def test_unit_limit_dataclass_is_hashable():
    assert hash(Limit("min", 5.0, None, "mg/l"))


def test_brief_never_drops_data_gap_warning():
    res = score_ghats(R, L, festival="Durga")
    md = to_markdown(res, "en", "Durga")
    bairagarh = md.split("## 1.")[1].split("## 2.")[0]
    assert "No Durga 2025 test table" in bairagarh and "NOT counted as clean" in bairagarh


def test_latest_check_uses_newest_festival_test_and_flags_breaches():
    from visarjan.summary import latest_check
    site = [s for s in R.site.unique() if s.startswith("Bairagarh")][0]
    year, table = latest_check(R, L, site, "Durga")
    assert year == 2024  # no Durga 2025 table for Bairagarh
    assert set(table) == {"pH", "Dissolved oxygen", "BOD"}
    assert all(state in ("ok", "violation", "missing") for row in table.values() for _, state in row.values())
    other = [s for s in R.site.unique() if s.startswith("Shahpura")][0]
    assert latest_check(R, L, other, "Durga")[0] == 2025
    assert latest_check(R, L, site, "NoSuchFestival") == (None, {})


def test_export_is_valid_json_with_all_ghats_and_both_languages():
    import json
    from visarjan.export import build
    data, briefs = build()
    json.dumps(data, allow_nan=False)  # no NaN leaks into the front end
    assert set(briefs) == {"durga", "all"}
    for key in ("durga", "all"):
        assert len(data["variants"][key]) == 7
        for g in data["variants"][key]:
            assert len(g["reasons_text"]["en"]) == len(g["reasons_text"]["hi"]) == len(g["reasons"])
            assert g["site"] in data["latest"] and g["site"] in data["readings"]
