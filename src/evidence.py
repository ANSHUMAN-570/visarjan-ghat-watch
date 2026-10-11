"""Traceability: every number on the dashboard can be listed as source rows with file and page citations."""
from __future__ import annotations

import pandas as pd

from .data_loader import KEY_PARAMETERS, PHASE_ORDER
from .metrics import with_benchmark

NO_PAGE = {"en": "Source page not verified", "hi": "स्रोत पृष्ठ सत्यापित नहीं"}


def citation(source_file, page, lang: str = "en") -> str:
    """'<report file>, p.<page>' - or 'Source page not verified'. A page is never guessed."""
    if page is None or pd.isna(page):
        return NO_PAGE[lang] if source_file is None or pd.isna(source_file) else f"{source_file} ({NO_PAGE[lang]})"
    if source_file is None or pd.isna(source_file):
        return f"p.{int(page)}"
    return f"{source_file}, p.{int(page)}"


def observation_rows(df: pd.DataFrame, cfg: dict, lang: str = "en") -> pd.DataFrame:
    """Long evidence table: one row per observation with its original text, status, benchmark result and citation."""
    d = with_benchmark(df, cfg)
    out = pd.DataFrame({
        "site": d["site"], "site_original": d["site_original"], "year": d["year"], "festival": d["festival"],
        "phase": d["phase"].astype(str), "parameter": d["parameter"], "reported_result": d["reported_result"],
        "qualifier": d["qualifier"], "value": d["value"], "unit": d["unit"], "status": d["status"],
        "benchmark": d["benchmark"], "counts_toward_score": d["benchmark"] != "not_scored",
        "source_file": d["source_file"], "source_page": d["source_page"],
        "citation": [citation(f, p, lang) for f, p in zip(d["source_file"], d["source_page"])],
        "site_match_confidence": d["site_match_confidence"], "needs_review": d["review_flag"],
    })
    return out.sort_values(["site", "year", "festival", "parameter", "phase"], kind="mergesort").reset_index(drop=True)


def wide_view(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """One row per site/year/festival/phase with DO, BOD and pH as printed in the report (qualifiers kept)."""
    d = with_benchmark(df[df["parameter"].isin(KEY_PARAMETERS)], cfg)
    mark = {"within": "✓", "beyond": "✗", "not_scored": "–"}
    d = d.assign(cell=[f"{(r if r else '(blank)')} {mark[b]}" for r, b in zip(d["reported_result"], d["benchmark"])])
    wide = d.pivot_table(index=["site", "year", "festival", "phase"], columns="parameter", values="cell",
                         aggfunc="first", observed=True)
    wide = wide.reindex(columns=[p for p in KEY_PARAMETERS if p in wide.columns]).reset_index()
    wide["phase"] = pd.Categorical(wide["phase"].astype(str), PHASE_ORDER, ordered=True)
    return wide.sort_values(["site", "year", "festival", "phase"]).reset_index(drop=True)


def site_detail(df: pd.DataFrame, cfg: dict, site: str) -> dict:
    """Rows behind one site's score, plus per-year and per-parameter violation counts."""
    obs = observation_rows(df[df["site"] == site], cfg)
    key = obs[obs["parameter"].isin(KEY_PARAMETERS)]
    contributing = key[key["counts_toward_score"]]
    by_year = (contributing.assign(beyond=contributing["benchmark"] == "beyond")
               .groupby(["parameter", "year"]).agg(valid=("beyond", "size"), beyond=("beyond", "sum")).reset_index())
    return {"observations": obs, "contributing": contributing,
            "not_scored": key[~key["counts_toward_score"]], "by_year": by_year}


def key_findings(df: pd.DataFrame, cfg: dict, site: str, lang: str = "en") -> list[dict]:
    """Per key parameter: counts and the single worst valid reading, with its citation."""
    obs = observation_rows(df[df["site"] == site], cfg, lang)
    out = []
    for p in KEY_PARAMETERS:
        g = obs[(obs["parameter"] == p) & obs["counts_toward_score"]]
        if g.empty:
            out.append({"parameter": p, "n_valid": 0, "n_beyond": 0, "worst": None})
            continue
        b = cfg["benchmark"]["parameters"][p]
        beyond = g[g["benchmark"] == "beyond"]
        worst = None
        if len(beyond):
            if b["rule"] == "min":
                row = beyond.loc[beyond["value"].idxmin()]
            elif b["rule"] == "max":
                row = beyond.loc[beyond["value"].idxmax()]
            else:
                row = beyond.loc[(beyond["value"] - (b["min"] + b["max"]) / 2).abs().idxmax()]
            worst = {"value": float(row["value"]), "year": int(row["year"]), "festival": row["festival"],
                     "phase": row["phase"], "citation": row["citation"]}
        out.append({"parameter": p, "n_valid": len(g), "n_beyond": len(beyond), "worst": worst})
    return out


def coverage_gaps(df: pd.DataFrame) -> dict[str, list[tuple[int, str]]]:
    """For each site: (year, festival) test events that exist for other sites in `df` but have no rows for this site."""
    events = {(int(y), str(f)) for y, f in zip(df["year"], df["festival"]) if pd.notna(y)}
    gaps = {}
    for site, g in df.groupby("site"):
        have = {(int(y), str(f)) for y, f in zip(g["year"], g["festival"]) if pd.notna(y)}
        missing = sorted(events - have)
        if missing:
            gaps[site] = missing
    return gaps
