"""Export scored results as JSON (+ printable briefs) for the static JavaScript front end in web/.

    python -m visarjan.export            # writes web/data.json, web/brief_durga.html, web/brief_all.html
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from .brief import to_html
from .data import KEY_PARAMS, load_limits, load_readings
from .i18n import APP, UI, render_reason
from .summary import latest_check

WEB = Path(__file__).resolve().parent.parent / "web"
VARIANTS = {"durga": "Durga", "all": None}


def build() -> tuple[dict, dict[str, str]]:
    from .scoring import score_ghats

    readings, limits = load_readings(), load_limits()
    variants: dict[str, list[dict]] = {}
    briefs: dict[str, str] = {}
    for key, festival in VARIANTS.items():
        results = score_ghats(readings, limits, festival)
        briefs[key] = to_html(results, ("en", "hi"), festival)
        out = []
        for g in results:
            d = dataclasses.asdict(g)
            d["reasons_text"] = {lang: [render_reason(r, lang) for r in g.reasons] for lang in UI}
            d["reason_types"] = [r["type"] for r in g.reasons]
            out.append(d)
        variants[key] = out

    sites = sorted(readings["site"].unique())
    latest = {}
    for s in sites:
        year, table = latest_check(readings, limits, s, "Durga")
        latest[s] = {"year": year, "table": {p: {ph: list(v) for ph, v in row.items()} for p, row in table.items()}}
    key_rows = readings[readings["parameter"].isin(KEY_PARAMS)].sort_values(["year", "festival", "parameter", "phase"])
    raw: dict[str, list[dict]] = {s: [] for s in sites}
    for r in key_rows.itertuples():
        raw[r.site].append({"year": int(r.year), "festival": r.festival, "phase": str(r.phase),
                            "parameter": r.parameter, "printed": None if r.value_as_printed != r.value_as_printed
                            else str(r.value_as_printed), "status": r.status,
                            "page": None if r.source_page != r.source_page else int(r.source_page)})
    data = {"variants": variants, "latest": latest, "readings": raw, "ui": UI, "app": APP,
            "visarjan_date": "2026-10-20"}
    return data, briefs


def main() -> None:
    data, briefs = build()
    WEB.mkdir(exist_ok=True)
    (WEB / "data.json").write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    for key, html in briefs.items():
        (WEB / f"brief_{key}.html").write_text(html, encoding="utf-8")
    print(f"Wrote {WEB / 'data.json'} and {len(briefs)} briefs")


if __name__ == "__main__":
    main()
