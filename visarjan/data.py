"""Loading and cleaning of the MPPCB ghat readings and the CPCB limits.

Missing-data rules (from the data dictionary):
  * ``BDL`` / ``ND``                  -> very low (not zero, not missing)
  * ``not sampled``, ``*``, ``**``,
    blank or ``_``                    -> missing, NEVER treated as clean
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
READINGS_CSV = DATA_DIR / "bhopal_ghats_2023_2025.csv"
CRITERIA_CSV = DATA_DIR / "cpcb_water_quality_criteria.csv"

PHASE_ORDER = ["pre", "during", "after"]
VERY_LOW_FLAGS = {"BDL", "ND"}

# Parameters that have a CPCB Class B (outdoor bathing) limit AND appear in the data.
KEY_PARAMS = ["pH", "Dissolved oxygen", "BOD"]
_CRITERIA_NAME = {"pH": "pH", "Dissolved oxygen": "Dissolved oxygen", "BOD (5 days 20C)": "BOD"}


@dataclass(frozen=True)
class Limit:
    kind: str  # "min", "max" or "range"
    lo: float | None
    hi: float | None
    unit: str


def load_readings(path: Path | str = READINGS_CSV) -> pd.DataFrame:
    """Return the readings with a ``status`` column: value | very_low | missing."""
    df = pd.read_csv(path, encoding="utf-8", encoding_errors="replace")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    flag = df["flag"].fillna("").astype(str).str.strip().str.upper()
    df["status"] = "missing"
    df.loc[df["value"].notna(), "status"] = "value"
    df.loc[df["value"].isna() & flag.isin(VERY_LOW_FLAGS), "status"] = "very_low"
    df["phase"] = pd.Categorical(df["phase"], PHASE_ORDER, ordered=True)
    return df


def load_limits(path: Path | str = CRITERIA_CSV, cls: str = "B") -> dict[str, Limit]:
    """CPCB limits for one water class, keyed by the parameter name used in the readings."""
    c = pd.read_csv(path, dtype=str)
    c = c[c["class"] == cls]
    limits: dict[str, Limit] = {}
    for _, r in c.iterrows():
        name = _CRITERIA_NAME.get(r["parameter"])
        if name is None:
            continue  # e.g. total coliform: a limit exists but the dataset has no coliform readings
        unit = r["unit"] if isinstance(r["unit"], str) else ""
        if r["limit_type"] == "range":
            lo, hi = (float(x) for x in r["limit"].split("-"))
            limits[name] = Limit("range", lo, hi, unit)
        elif r["limit_type"] == "min":
            limits[name] = Limit("min", float(r["limit"]), None, unit)
        else:
            limits[name] = Limit("max", None, float(r["limit"]), unit)
    missing = [p for p in KEY_PARAMS if p not in limits]
    if missing:
        raise ValueError(f"No class {cls} limit found for: {missing}")
    return limits
