"""Transparent risk scoring of ghats against CPCB Class B (outdoor bathing) limits.

Score (0-100) = 100 * (W_VIOLATION * violation_rate
                     + W_SEVERITY  * severity
                     + W_IMPACT    * worse_during_immersion_rate)

* violation_rate : share of readings breaking a limit (pH, dissolved oxygen, BOD),
                   half the average over the three parameters, half the worst parameter;
                   newer years weigh more.
* severity       : how far readings are beyond the limit (0 = within, 1 = far beyond).
* impact rate    : share of before/during/after test series where oxygen fell by
                   >= IMPACT_DELTA mg/l or BOD rose by >= IMPACT_DELTA mg/l.
                   This is an observation, not proof of cause.

Missing readings are NEVER counted as clean: they are excluded from the rates and
reported separately as a data gap (coverage, missing festival tables).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .data import KEY_PARAMS, Limit

W_VIOLATION, W_SEVERITY, W_IMPACT = 0.50, 0.30, 0.20
IMPACT_DELTA = 1.0  # mg/l change that counts as "worse during/after immersion"
TIER_HIGH, TIER_MEDIUM = 65.0, 45.0
LOW_COVERAGE = 0.85  # below this share of expected key readings -> low confidence
CLEAN_BOD_RATE = 0.5  # share of BOD readings over limit that triggers a cleaning action
AERATE_DO_RATE = 0.3  # share of DO readings under limit that triggers an aeration action
RETEST_PH_RATE = 0.3


@dataclass
class ParamStat:
    parameter: str
    n_obs: int
    n_violations: int
    worst_value: float | None
    worst_year: int | None = None
    worst_festival: str | None = None
    worst_phase: str | None = None
    worst_page: int | None = None
    n_zero: int = 0


@dataclass
class GhatResult:
    site: str
    water_body: str
    score: float
    tier: str  # "high" | "medium" | "low"
    components: dict[str, float]
    params: dict[str, ParamStat]
    reasons: list[dict]
    actions: list[str]
    coverage: float
    low_confidence: bool
    missing_events: list[tuple[int, str]] = field(default_factory=list)
    n_missing_readings: int = 0
    n_expected_readings: int = 0
    rank: int = 0


def evaluate(status: str, value: float, limit: Limit) -> tuple[str, float]:
    """Return (state, severity) for one reading. state: ok | violation | missing."""
    if status == "missing":
        return "missing", 0.0
    if status == "very_low":
        if limit.kind == "min":  # oxygen below detection = effectively none
            return "violation", 1.0
        if limit.kind == "max":  # BDL against a maximum is within the limit
            return "ok", 0.0
        return "missing", 0.0  # a range limit cannot be judged from "very low"
    if limit.kind == "min":
        dist = max(limit.lo - value, 0.0)
        norm = limit.lo
    elif limit.kind == "max":
        dist = max(value - limit.hi, 0.0)
        norm = limit.hi
    else:
        dist = max(limit.lo - value, value - limit.hi, 0.0)
        norm = 1.0  # one pH unit outside the range = maximum severity
    if dist <= 0:
        return "ok", 0.0
    return "violation", min(dist / norm, 1.0)


def _prepare(readings: pd.DataFrame, limits: dict[str, Limit], festival: str | None,
             years: list[int] | None) -> pd.DataFrame:
    df = readings[readings["parameter"].isin(KEY_PARAMS)].copy()
    if festival:
        df = df[df["festival"] == festival]
    if years:
        df = df[df["year"].isin(years)]
    if df.empty:
        return df
    results = [evaluate(s, v, limits[p]) for s, v, p in zip(df["status"], df["value"], df["parameter"])]
    df["state"] = [r[0] for r in results]
    df["severity"] = [r[1] for r in results]
    df["weight"] = df["year"] - df["year"].min() + 1  # newer years count more
    return df


def _impact(site_df: pd.DataFrame) -> tuple[int, int, float]:
    """(worsened series, tested series, weighted rate) for oxygen and BOD before vs during/after."""
    num = den = 0.0
    worse = total = 0
    vals = site_df[(site_df["status"] == "value") & site_df["parameter"].isin(["Dissolved oxygen", "BOD"])]
    for (year, _fest, param), g in vals.groupby(["year", "festival", "parameter"], observed=True):
        by_phase = {ph: v for ph, v in zip(g["phase"].astype(str), g["value"])}
        pre = by_phase.get("pre")
        later = [by_phase[p] for p in ("during", "after") if p in by_phase]
        if pre is None or not later:
            continue
        if param == "Dissolved oxygen":
            bad = pre - min(later) >= IMPACT_DELTA
        else:
            bad = max(later) - pre >= IMPACT_DELTA
        w = float(g["weight"].iloc[0])
        total += 1
        worse += int(bad)
        den += w
        num += w * bad
    return worse, total, (num / den if den else 0.0)


def _param_stat(p: str, g: pd.DataFrame, limit: Limit) -> ParamStat | None:
    obs = g[g["state"] != "missing"]
    if obs.empty:
        return None
    viol = obs[obs["state"] == "violation"]
    stat = ParamStat(p, len(obs), len(viol), None)
    num = obs[obs["status"] == "value"]
    stat.n_zero = int((num["value"] == 0).sum()) if p == "Dissolved oxygen" else 0
    if len(viol) and not viol["value"].dropna().empty:
        # worst = furthest beyond the limit in the violating direction
        v = viol.dropna(subset=["value"])
        if limit.kind == "min":
            row = v.loc[v["value"].idxmin()]
        elif limit.kind == "max":
            row = v.loc[v["value"].idxmax()]
        else:
            row = v.loc[v["severity"].idxmax()]
        stat.worst_value = float(row["value"])
        stat.worst_year = int(row["year"])
        stat.worst_festival = str(row["festival"])
        stat.worst_phase = str(row["phase"])
        stat.worst_page = int(row["source_page"]) if pd.notna(row["source_page"]) else None
    return stat


def score_ghats(readings: pd.DataFrame, limits: dict[str, Limit], festival: str | None = None,
                years: list[int] | None = None) -> list[GhatResult]:
    """Score and rank every ghat. Highest risk first."""
    df = _prepare(readings, limits, festival, years)
    if df.empty:
        return []
    events = sorted({(int(y), str(f)) for y, f in zip(df["year"], df["festival"])})
    expected = len(events) * len(KEY_PARAMS) * 3  # events x parameters x phases
    out: list[GhatResult] = []

    for site, sdf in df.groupby("site"):
        water_body = str(sdf["water_body"].iloc[0])
        have = {(int(y), str(f)) for y, f in zip(sdf["year"], sdf["festival"])}
        missing_events = [e for e in events if e not in have]
        n_obs = int((sdf["state"] != "missing").sum())
        coverage = n_obs / expected if expected else 0.0

        params: dict[str, ParamStat] = {}
        v_rates: list[float] = []
        sevs: list[float] = []
        for p in KEY_PARAMS:
            g = sdf[sdf["parameter"] == p]
            obs = g[g["state"] != "missing"]
            if obs.empty:
                continue
            w = obs["weight"]
            v_rates.append(float((w * (obs["state"] == "violation")).sum() / w.sum()))
            sevs.append(float((w * obs["severity"]).sum() / w.sum()))
            stat = _param_stat(p, g, limits[p])
            if stat:
                params[p] = stat
        # half average, half worst parameter: one clean parameter must not hide a failing one
        violation = (0.5 * sum(v_rates) / len(v_rates) + 0.5 * max(v_rates)) if v_rates else 0.0
        severity = (0.5 * sum(sevs) / len(sevs) + 0.5 * max(sevs)) if sevs else 0.0
        n_worse, n_series, impact = _impact(sdf)

        score = 100.0 * (W_VIOLATION * violation + W_SEVERITY * severity + W_IMPACT * impact)
        tier = "high" if score >= TIER_HIGH else "medium" if score >= TIER_MEDIUM else "low"

        def rate(p: str) -> float:
            s = params.get(p)
            return s.n_violations / s.n_obs if s else 0.0

        reasons: list[dict] = []
        do = params.get("Dissolved oxygen")
        if do and do.n_zero:
            reasons.append({"type": "zero_do", "n": do.n_zero})
        for key, p in (("do_low", "Dissolved oxygen"), ("bod_high", "BOD"), ("ph_out", "pH")):
            s = params.get(p)
            if s and s.n_violations:
                reasons.append({"type": key, "v": s.n_violations, "n": s.n_obs, "worst": s.worst_value,
                                "year": s.worst_year, "festival": s.worst_festival,
                                "phase": s.worst_phase, "page": s.worst_page})
        if n_worse:
            reasons.append({"type": "worse_during", "v": n_worse, "n": n_series})
        for year, fest in missing_events:
            reasons.append({"type": "gap_event", "year": year, "festival": fest})
        n_missing = expected - n_obs  # not sampled in a table, or the whole table is absent
        if n_missing:
            reasons.append({"type": "gap_missing", "n": n_missing, "total": expected})

        low_conf = coverage < LOW_COVERAGE or bool(missing_events)
        actions: list[str] = []
        if rate("BOD") >= CLEAN_BOD_RATE:
            actions.append("clean")
        if rate("Dissolved oxygen") >= AERATE_DO_RATE:
            actions.append("aerate")
        if tier != "low" or low_conf or rate("pH") >= RETEST_PH_RATE:
            actions.append("retest")
        if not actions:
            actions.append("monitor")

        out.append(GhatResult(
            site=str(site), water_body=water_body, score=round(score, 1), tier=tier,
            components={"violation": violation, "severity": severity, "impact": impact},
            params=params, reasons=reasons, actions=actions, coverage=coverage,
            low_confidence=low_conf, missing_events=missing_events,
            n_missing_readings=n_missing, n_expected_readings=expected,
        ))

    out.sort(key=lambda r: (-r.score, r.site))
    for i, r in enumerate(out, 1):
        r.rank = i
    return out
