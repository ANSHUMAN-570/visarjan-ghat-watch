"""Transparent, deterministic site prioritisation.

score = 100 * sum(w_p * violation_rate_p) / sum(w_p)   over parameters with >= 1 valid reading.

* Weights come from config/thresholds.yaml and are ILLUSTRATIVE (not official, not a health-risk formula).
* A parameter with no valid reading is dropped and the remaining weights renormalised; it is never 0 violations.
* A site with too few valid readings is "Insufficient evidence - retest" and gets no score (never 0, never "safe").
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data_loader import KEY_PARAMETERS
from .metrics import parameter_summary

SCORED, INSUFFICIENT = "scored", "insufficient"


def rank_sites(df: pd.DataFrame, cfg: dict, sites: list[str] | None = None) -> pd.DataFrame:
    """One row per site, ranked. `sites` lists sites that must appear even if `df` has no rows for them."""
    summary = parameter_summary(df, cfg)
    weights = cfg["weights"]
    min_valid = cfg["scoring"]["min_valid_readings_per_site"]
    low_n = cfg["scoring"]["low_sample_threshold"]
    names = sorted(set(sites if sites is not None else df["site"].unique()))

    rows = []
    for site in names:
        s = summary[summary["site"] == site].set_index("parameter")
        per, usable_w = {}, {}
        for p in KEY_PARAMETERS:
            r = s.loc[p] if p in s.index else None
            n_valid = int(r["n_valid"]) if r is not None else 0
            per[p] = {"n_valid": n_valid, "n_beyond": int(r["n_beyond"]) if r is not None else 0,
                      "rate": float(r["violation_rate"]) if r is not None and n_valid else np.nan}
            if n_valid:
                usable_w[p] = weights[p]
        total_valid = sum(v["n_valid"] for v in per.values())
        scored = total_valid >= min_valid and bool(usable_w)
        wsum = sum(usable_w.values())
        score = (100.0 * sum(usable_w[p] / wsum * per[p]["rate"] for p in usable_w)) if scored else np.nan
        years = sorted({y for p in KEY_PARAMETERS if p in s.index for y in s.loc[p, "years"]})
        n_rows = int(s["n_rows"].sum()) if len(s) else 0
        row = {
            "site": site, "ranking_status": SCORED if scored else INSUFFICIENT, "score": score,
            "n_valid": total_valid, "n_not_scored": int(s["n_not_scored"].sum()) if len(s) else 0,
            "completeness": total_valid / n_rows if n_rows else np.nan,
            "years": years, "latest_year": max(years) if years else None,
            "weights_used": {p: usable_w[p] / wsum for p in usable_w} if scored else {},
            "params_without_data": [p for p in KEY_PARAMETERS if per[p]["n_valid"] == 0],
            "low_sample": bool(scored and any(0 < per[p]["n_valid"] < low_n for p in KEY_PARAMETERS)),
        }
        for p in KEY_PARAMETERS:
            k = cfg["benchmark"]["parameters"][p]["short"]
            row.update({f"{k}_n_valid": per[p]["n_valid"], f"{k}_n_beyond": per[p]["n_beyond"],
                        f"{k}_rate": per[p]["rate"]})
        rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        return out.assign(rank=pd.Series(dtype="Int64"))
    # deterministic order: scored sites by score desc then name; insufficient evidence last, by name
    out["_s"] = out["score"].fillna(-1.0)
    out = out.sort_values(["_s", "site"], ascending=[False, True], kind="mergesort").drop(columns="_s")
    out = out.reset_index(drop=True)
    out["rank"] = pd.Series([i + 1 if st == SCORED else pd.NA for i, st in enumerate(out["ranking_status"])],
                            dtype="Int64")
    return out
