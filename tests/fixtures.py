"""SYNTHETIC test fixtures. Every site here is named 'SYNTHETIC ...' so it can never be mistaken for real MPPCB data."""
from __future__ import annotations

import pandas as pd

from src.data_loader import load_config, to_canonical

CFG = load_config()
RAW_COLUMNS = ["year", "festival", "site", "water_body", "phase", "parameter", "value", "unit_assumed", "flag",
               "value_as_printed", "site_as_printed", "site_match_confidence", "source_page"]
UNITS = {"Dissolved oxygen": "mg/l", "BOD": "mg/l", "pH": ""}


def row(site="SYNTHETIC A", parameter="Dissolved oxygen", value="4.0", flag="", year=2025, festival="Durga",
        phase="pre", unit=None, printed=None, page="10", confidence="high"):
    printed = value if printed is None else printed
    return [str(year), festival, site, "SYNTHETIC LAKE", phase, parameter, value, UNITS[parameter] if unit is None else unit,
            flag, printed, f"{site} (as printed)", confidence, page]


def canonical(rows: list[list]) -> pd.DataFrame:
    raw = pd.DataFrame(rows, columns=RAW_COLUMNS).replace("", pd.NA)
    return to_canonical(raw, CFG)


def site_rows(site: str, do: list, bod: list, ph: list, year: int = 2025) -> list[list]:
    """Rows for one synthetic site; each list holds values as strings ('' = blank, 'BDL', 'ND', ...)."""
    out = []
    for param, vals in (("Dissolved oxygen", do), ("BOD", bod), ("pH", ph)):
        for i, v in enumerate(vals):
            flag = v if v in ("BDL", "ND", "not sampled") else ""
            out.append(row(site, param, "" if flag or v == "" else v, flag, year=year, phase=["pre", "during", "after"][i % 3],
                           festival="Durga" if i < 3 else "Ganesh", printed=v))
    return out
