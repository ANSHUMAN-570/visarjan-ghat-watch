"""Latest-test summary: the most recent test of one festival at one ghat, judged against the limits."""
from __future__ import annotations

import pandas as pd

from .data import KEY_PARAMS, PHASE_ORDER, Limit
from .scoring import evaluate


def latest_check(readings: pd.DataFrame, limits: dict[str, Limit], site: str,
                 festival: str = "Durga") -> tuple[int | None, dict[str, dict[str, tuple[str, str]]]]:
    """Return (year, {parameter: {phase: (text, state)}}) for the newest festival test with any usable reading.

    state is ok | violation | missing, so the caller can mark limit breaches and show gaps as gaps.
    """
    df = readings[(readings["site"] == site) & (readings["festival"] == festival)
                  & readings["parameter"].isin(KEY_PARAMS)]
    for year in sorted(df["year"].unique(), reverse=True):
        ydf = df[df["year"] == year]
        table: dict[str, dict[str, tuple[str, str]]] = {}
        usable = False
        for p in KEY_PARAMS:
            row: dict[str, tuple[str, str]] = {}
            for ph in PHASE_ORDER:
                m = ydf[(ydf["parameter"] == p) & (ydf["phase"].astype(str) == ph)]
                if m.empty:
                    row[ph] = ("missing", "missing")
                    continue
                r = m.iloc[0]
                state, _ = evaluate(r["status"], r["value"], limits[p])
                usable |= state != "missing"
                text = "missing" if state == "missing" else ("below detection" if r["status"] == "very_low"
                                                             else f"{r['value']:g}")
                row[ph] = (text, state)
            table[p] = row
        if usable:
            return int(year), table
    return None, {}
