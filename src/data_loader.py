"""Load the configuration and the readings file into one canonical, traceable table.

Canonical columns (see docs/data_dictionary.md):
site, site_original, water_body, site_match_confidence, review_flag, year, festival, phase, parameter, value, unit,
status, qualifier, reported_result, source_file, source_url, source_page
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from .data_validation import (Issue, classify_status, normalise_unit, is_plausible, unit_matches,
                              validate_canonical, validate_raw_columns)

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "thresholds.yaml"
DEFAULT_DATA = ROOT / "data" / "raw" / "bhopal_ghats_2023_2025.csv"
KEY_PARAMETERS = ["Dissolved oxygen", "BOD", "pH"]
PHASE_ORDER = ["pre", "during", "after"]


def load_config(path: Path | str = CONFIG_PATH) -> dict:
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    cfg["sources"] = {int(k): v for k, v in cfg.get("sources", {}).items()}
    total = sum(cfg["weights"].values())
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"weights in {path} must sum to 1.0 (got {total})")
    return cfg


def to_canonical(raw: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    validate_raw_columns(raw)
    df = pd.DataFrame({
        "site": raw["site"].astype(str).str.strip(),
        "site_original": raw["site_as_printed"].astype(str).str.strip(),
        "water_body": raw["water_body"].astype(str).str.strip(),
        "site_match_confidence": raw["site_match_confidence"].astype(str).str.strip().str.lower(),
        "year": pd.to_numeric(raw["year"], errors="coerce").astype("Int64"),
        "festival": raw["festival"].astype(str).str.strip(),
        "phase": raw["phase"].astype(str).str.strip().str.lower(),
        "parameter": raw["parameter"].astype(str).str.strip(),
        "value": pd.to_numeric(raw["value"], errors="coerce"),
        "unit": raw["unit_assumed"].map(normalise_unit),
        "qualifier": raw["flag"].fillna("").astype(str).str.strip(),
        "reported_result": raw["value_as_printed"].map(lambda v: "" if pd.isna(v) else str(v).strip()),
        "source_page": pd.to_numeric(raw["source_page"], errors="coerce").astype("Int64"),
    })
    df["review_flag"] = df["site_match_confidence"] != "high"
    df["status"] = [classify_status(v, rep, q) for v, rep, q in zip(df["value"], df["reported_result"], df["qualifier"])]

    # Units: a measured benchmark parameter whose unit does not match is kept but never scored.
    bad_unit = (df["status"] == "measured") & ~pd.Series(
        [unit_matches(p, u, cfg) for p, u in zip(df["parameter"], df["unit"])], index=df.index)
    df.loc[bad_unit, "status"] = "invalid_unit"
    # Plausibility: impossible numbers (e.g. pH 40, negative BOD) are kept but never scored.
    implausible = (df["status"] == "measured") & pd.Series(
        [not is_plausible(p, v, cfg) for p, v in zip(df["parameter"], df["value"])], index=df.index)
    df.loc[implausible, "status"] = "invalid"

    df["source_file"] = df["year"].map(lambda y: cfg["sources"].get(int(y), {}).get("file") if pd.notna(y) else None)
    df["source_url"] = df["year"].map(lambda y: cfg["sources"].get(int(y), {}).get("url") if pd.notna(y) else None)
    df["phase"] = pd.Categorical(df["phase"], PHASE_ORDER, ordered=True)
    return df


def load_dataset(path: Path | str = DEFAULT_DATA, cfg: dict | None = None) -> tuple[pd.DataFrame, list[Issue], dict]:
    """Return (canonical dataframe, validation issues, config)."""
    cfg = cfg or load_config()
    raw = pd.read_csv(path, encoding="utf-8", encoding_errors="replace", dtype=str, keep_default_na=False,
                      na_values=[""])
    df = to_canonical(raw, cfg)
    return df, validate_canonical(df, cfg), cfg
