import pandas as pd
import pytest

from src.data_loader import load_dataset, to_canonical
from src.data_validation import DataValidationError, classify_status, validate_canonical, validate_raw_columns
from src.evidence import citation

from .fixtures import CFG, RAW_COLUMNS, canonical, row


# ---- schema errors are loud, not silent ------------------------------------------------------------------
def test_missing_column_raises_with_the_column_name():
    raw = pd.DataFrame([row()], columns=RAW_COLUMNS).drop(columns=["source_page"])
    with pytest.raises(DataValidationError, match="source_page"):
        validate_raw_columns(raw)


def test_empty_input_raises():
    with pytest.raises(DataValidationError, match="no rows"):
        validate_raw_columns(pd.DataFrame(columns=RAW_COLUMNS))


# ---- missing / qualifier handling (data-integrity rules 1-4) ---------------------------------------------
@pytest.mark.parametrize("value,reported,qualifier,expected", [
    (4.2, "4.2", "", "measured"),
    (float("nan"), "BDL", "BDL", "bdl"),
    (float("nan"), "ND", "ND", "nd"),
    (float("nan"), "", "not sampled", "not_sampled"),
    (float("nan"), "*", "*", "not_sampled"),
    (float("nan"), "_", "", "missing"),
    (float("nan"), "", "", "missing"),
    (float("nan"), "abc", "", "invalid"),
])
def test_classify_status(value, reported, qualifier, expected):
    assert classify_status(value, reported, qualifier) == expected


def test_nd_and_bdl_stay_distinct():
    assert classify_status(float("nan"), "ND", "ND") != classify_status(float("nan"), "BDL", "BDL")


def test_bdl_is_preserved_never_converted_to_zero():
    df = canonical([row(parameter="BOD", value="", flag="BDL", printed="BDL")])
    r = df.iloc[0]
    assert pd.isna(r["value"]) and r["status"] == "bdl" and r["qualifier"] == "BDL" and r["reported_result"] == "BDL"


def test_blank_is_missing_not_zero():
    df = canonical([row(value="", flag="", printed="")])
    assert pd.isna(df.iloc[0]["value"]) and df.iloc[0]["status"] == "missing"


# ---- invalid numbers and units ---------------------------------------------------------------------------
def test_unreadable_text_is_flagged_not_dropped():
    df = canonical([row(value="", flag="", printed="12..5")])
    assert len(df) == 1 and df.iloc[0]["status"] == "invalid"
    assert any(i.code == "invalid_value" for i in validate_canonical(df, CFG))


def test_unit_mismatch_is_excluded_and_reported():
    df = canonical([row(parameter="Dissolved oxygen", value="6", unit="mg/kg")])
    assert df.iloc[0]["status"] == "invalid_unit"
    assert any(i.code == "unit_mismatch" and i.severity == "error" for i in validate_canonical(df, CFG))


def test_equivalent_unit_spelling_is_accepted():
    assert canonical([row(value="6", unit="MG/L")]).iloc[0]["status"] == "measured"


@pytest.mark.parametrize("param,value", [("pH", "40"), ("pH", "-1"), ("BOD", "-2"), ("Dissolved oxygen", "-0.5")])
def test_implausible_numbers_are_invalid(param, value):
    assert canonical([row(parameter=param, value=value)]).iloc[0]["status"] == "invalid"


# ---- mapping and sources ---------------------------------------------------------------------------------
def test_low_confidence_site_mapping_is_flagged_and_original_name_kept():
    df = canonical([row(site="SYNTHETIC B", confidence="medium")])
    assert df.iloc[0]["review_flag"] and df.iloc[0]["site_original"] == "SYNTHETIC B (as printed)"
    assert any(i.code == "site_mapping_review" for i in validate_canonical(df, CFG))


def test_missing_page_is_never_invented():
    df = canonical([row(page="")])
    assert pd.isna(df.iloc[0]["source_page"])
    assert "Source page not verified" in citation(df.iloc[0]["source_file"], df.iloc[0]["source_page"])
    assert any(i.code == "page_unverified" for i in validate_canonical(df, CFG))


def test_year_without_configured_report_is_reported():
    df = canonical([row(year=2019)])
    assert pd.isna(df.iloc[0]["source_file"])
    assert any(i.code == "no_source_file" for i in validate_canonical(df, CFG))


def test_duplicate_keys_are_warned_about():
    df = canonical([row(), row()])
    assert any(i.code == "duplicate_rows" for i in validate_canonical(df, CFG))


# ---- real dataset ----------------------------------------------------------------------------------------
def test_real_dataset_loads_without_errors_and_keeps_every_row():
    df, issues, _ = load_dataset()
    assert len(df) == 1524
    assert not [i for i in issues if i.severity == "error"]
    assert set(df["status"]) <= {"measured", "bdl", "nd", "not_sampled", "missing", "invalid", "invalid_unit"}
    assert df.loc[df["qualifier"] == "BDL", "value"].isna().all()
    assert df["source_file"].notna().all()


def test_weights_must_sum_to_one(tmp_path):
    from src.data_loader import load_config
    bad = (tmp_path / "t.yaml")
    bad.write_text("weights: {Dissolved oxygen: 0.5, BOD: 0.5, pH: 0.5}\nsources: {}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sum to 1.0"):
        load_config(bad)
