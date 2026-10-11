"""Benchmark comparison and per-site / per-parameter statistics. Only status == "measured" rows are ever scored."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data_loader import KEY_PARAMETERS


def benchmark_result(parameter: str, value: float, cfg: dict) -> str:
    """'within' | 'beyond' for one numeric value (limits are inclusive); 'not_scored' without a benchmark."""
    b = cfg["benchmark"]["parameters"].get(parameter)
    if b is None or pd.isna(value):
        return "not_scored"
    if b["rule"] == "min":
        ok = value >= b["value"]
    elif b["rule"] == "max":
        ok = value <= b["value"]
    else:
        ok = b["min"] <= value <= b["max"]
    return "within" if ok else "beyond"


def with_benchmark(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Add `benchmark`: within / beyond for measured benchmark parameters, otherwise not_scored.

    BDL, ND, not sampled, blank and invalid results are never given a number, so they stay not_scored.
    """
    out = df.copy()
    out["benchmark"] = [
        benchmark_result(p, v, cfg) if s == "measured" else "not_scored"
        for p, v, s in zip(out["parameter"], out["value"], out["status"])]
    return out


def parameter_summary(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """One row per site x key parameter present in `df`: valid count, violations, rate, coverage."""
    d = with_benchmark(df[df["parameter"].isin(KEY_PARAMETERS)], cfg)
    rows = []
    for (site, param), g in d.groupby(["site", "parameter"], observed=True, sort=True):
        valid = g[g["benchmark"] != "not_scored"]
        n_valid, n_beyond = len(valid), int((valid["benchmark"] == "beyond").sum())
        rows.append({
            "site": site, "parameter": param, "n_rows": len(g), "n_valid": n_valid, "n_beyond": n_beyond,
            "violation_rate": n_beyond / n_valid if n_valid else np.nan,
            "n_not_scored": len(g) - n_valid, "completeness": n_valid / len(g),
            "years": sorted(int(y) for y in valid["year"].dropna().unique()),
            "latest_year": int(valid["year"].max()) if n_valid else None,
        })
    cols = ["site", "parameter", "n_rows", "n_valid", "n_beyond", "violation_rate", "n_not_scored", "completeness",
            "years", "latest_year"]
    return pd.DataFrame(rows, columns=cols)


def overview(df: pd.DataFrame, cfg: dict) -> dict:
    """Headline numbers, all computed from `df`."""
    d = with_benchmark(df, cfg)
    key = d[d["parameter"].isin(KEY_PARAMETERS)]
    per_param = {}
    for p in KEY_PARAMETERS:
        g = key[key["parameter"] == p]
        valid = g[g["benchmark"] != "not_scored"]
        beyond = int((valid["benchmark"] == "beyond").sum())
        per_param[p] = {"n_valid": len(valid), "n_beyond": beyond, "n_rows": len(g),
                        "rate": beyond / len(valid) if len(valid) else np.nan}
    return {
        "n_sites": int(d["site"].nunique()), "n_rows": len(d), "n_key_rows": len(key),
        "years": sorted(int(y) for y in d["year"].dropna().unique()),
        "per_param": per_param,
        "n_unscorable_key": int((key["benchmark"] == "not_scored").sum()),
        "key_status_counts": key["status"].value_counts().to_dict(),
        "all_status_counts": d["status"].value_counts().to_dict(),
    }


def guide_check(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Compare the participant guide's reported figures with a recalculation from `df` (pass the UNFILTERED data)."""
    g = cfg["guide_reported"]
    d = with_benchmark(df, cfg)
    do = d[(d["parameter"] == "Dissolved oxygen") & (d["benchmark"] != "not_scored")]
    bod = d[(d["parameter"] == "BOD") & (d["benchmark"] != "not_scored")]
    z = g["bairagarh_do_zero"]
    zero = d[(d["site"] == z["site"]) & (d["parameter"] == "Dissolved oxygen") & (d["status"] == "measured")
             & (d["value"] == 0)]
    do_b, bod_b = int((do["benchmark"] == "beyond").sum()), int((bod["benchmark"] == "beyond").sum())
    zero_years = sorted(int(y) for y in zero["year"].unique())
    rows = [
        ("DO below benchmark", f"{g['do_below_benchmark']['count']} of {g['do_below_benchmark']['of']}",
         f"{do_b} of {len(do)}", (do_b, len(do)) == (g["do_below_benchmark"]["count"], g["do_below_benchmark"]["of"])),
        ("BOD above benchmark", f"{g['bod_above_benchmark']['count']} of {g['bod_above_benchmark']['of']}",
         f"{bod_b} of {len(bod)}", (bod_b, len(bod)) == (g["bod_above_benchmark"]["count"], g["bod_above_benchmark"]["of"])),
        ("Bairagarh DO = 0 mg/L", f"{z['count']} times ({z['years'][0]} and {z['years'][1]})",
         f"{len(zero)} times (years {zero_years})", len(zero) == z["count"] and zero_years == sorted(z["years"])),
    ]
    return pd.DataFrame(rows, columns=["figure", "guide_reported", "recalculated", "matches"])
