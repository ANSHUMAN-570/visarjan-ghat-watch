"""Validation of the raw readings file and of the canonical dataset.

Nothing is silently dropped: bad rows stay in the data with a non-"measured" status and every problem is
returned as an :class:`Issue` the dashboard can show.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

REQUIRED_RAW_COLUMNS = [
    "year", "festival", "site", "water_body", "phase", "parameter", "value", "unit_assumed", "flag",
    "value_as_printed", "site_as_printed", "site_match_confidence", "source_page",
]
VALID_PHASES = {"pre", "during", "after"}
QUALIFIER_STATUS = {"BDL": "bdl", "ND": "nd", "NOT SAMPLED": "not_sampled", "*": "not_sampled", "**": "not_sampled"}


class DataValidationError(ValueError):
    """The input cannot be used at all (for example, a required column is missing)."""


@dataclass(frozen=True)
class Issue:
    severity: str  # "error" | "warning" | "info"
    code: str
    message: str
    row: int | None = None


def validate_raw_columns(raw: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_RAW_COLUMNS if c not in raw.columns]
    if missing:
        raise DataValidationError(
            f"Input is missing required column(s): {', '.join(missing)}. "
            f"Expected columns: {', '.join(REQUIRED_RAW_COLUMNS)}. See docs/data_dictionary.md.")
    if raw.empty:
        raise DataValidationError("Input has the right columns but no rows.")


def normalise_unit(unit) -> str:
    """Lower-case unit with spaces removed; blank / NaN -> ''."""
    if unit is None or (isinstance(unit, float) and pd.isna(unit)):
        return ""
    return str(unit).strip().lower().replace(" ", "")


def unit_matches(parameter: str, unit: str, cfg: dict) -> bool:
    """True when `unit` is what the benchmark for `parameter` expects. Parameters without a benchmark pass."""
    bench = cfg["benchmark"]["parameters"].get(parameter)
    return True if bench is None else normalise_unit(unit) == normalise_unit(bench["unit"])


def is_plausible(parameter: str, value: float, cfg: dict) -> bool:
    """False for impossible numbers (e.g. pH 40, negative BOD). Parameters without configured limits pass."""
    lim = cfg.get("plausible", {}).get(parameter)
    return True if lim is None or pd.isna(value) else lim["min"] <= value <= lim["max"]


def classify_status(value, reported, qualifier: str) -> str:
    """measured | bdl | nd | not_sampled | missing | invalid  (never converts a qualifier into a number)."""
    q = (qualifier or "").strip().upper()
    if pd.notna(value):
        return "measured"
    if q in QUALIFIER_STATUS:
        return QUALIFIER_STATUS[q]
    printed = "" if reported is None or (isinstance(reported, float) and pd.isna(reported)) else str(reported).strip()
    if printed in ("", "_", "-"):
        return "missing"
    upper = printed.upper()
    if upper in QUALIFIER_STATUS:
        return QUALIFIER_STATUS[upper]
    return "invalid"  # printed text that is neither a number nor a known qualifier


def validate_canonical(df: pd.DataFrame, cfg: dict) -> list[Issue]:
    """Problems worth showing to the user. Does not modify `df`."""
    issues: list[Issue] = []
    for i, r in df[df["status"] == "invalid"].iterrows():
        issues.append(Issue("error", "invalid_value", f"Unreadable result '{r['reported_result']}' for "
                            f"{r['parameter']} at {r['site_original']} ({r['year']}); excluded from scoring.", int(i)))
    for i, r in df[df["status"] == "invalid_unit"].iterrows():
        issues.append(Issue("error", "unit_mismatch", f"Unit '{r['unit']}' does not match the benchmark unit for "
                            f"{r['parameter']} at {r['site_original']} ({r['year']}); excluded from scoring.", int(i)))
    for i, r in df[~df["phase"].isin(VALID_PHASES)].iterrows():
        issues.append(Issue("warning", "unknown_phase", f"Unknown phase '{r['phase']}'.", int(i)))
    dup = df.duplicated(["site", "year", "festival", "phase", "parameter"], keep=False)
    if dup.any():
        issues.append(Issue("warning", "duplicate_rows", f"{int(dup.sum())} rows share the same site, year, festival, "
                            "phase and parameter. Counts may double-count one reading; review before relying on them."))
    review = df[df["review_flag"]][["site", "site_match_confidence"]].drop_duplicates()
    for _, r in review.iterrows():
        issues.append(Issue("warning", "site_mapping_review", f"Site name mapping for '{r['site']}' has "
                            f"'{r['site_match_confidence']}' confidence - manual review recommended."))
    nopage = int(df["source_page"].isna().sum())
    if nopage:
        issues.append(Issue("warning", "page_unverified", f"{nopage} rows have no source page: shown as 'Source page not verified'."))
    unmapped = sorted(int(y) for y in df.loc[df["source_file"].isna(), "year"].unique())
    if unmapped:
        issues.append(Issue("warning", "no_source_file", f"No report file is configured for year(s) {unmapped}; "
                            "add them under `sources:` in config/thresholds.yaml."))
    return issues
