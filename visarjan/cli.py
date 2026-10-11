"""Command line: write the officer brief without starting the web app.

    python -m visarjan.cli --festival Durga --lang both --out brief.html
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .brief import to_html, to_markdown
from .data import load_limits, load_readings
from .scoring import score_ghats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Rank Bhopal visarjan ghats by water-quality risk.")
    ap.add_argument("--festival", choices=["Ganesh", "Durga"], help="only use this festival's tests")
    ap.add_argument("--years", type=int, nargs="*", help="only use these years")
    ap.add_argument("--lang", choices=["en", "hi", "both"], default="both")
    ap.add_argument("--format", choices=["html", "md"], default="html")
    ap.add_argument("--out", help="output file (default: print to stdout)")
    a = ap.parse_args(argv)

    results = score_ghats(load_readings(), load_limits(), a.festival, a.years)
    if not results:
        print("No data for this selection.", file=sys.stderr)
        return 1
    langs = ("en", "hi") if a.lang == "both" else (a.lang,)
    if a.format == "html":
        text = to_html(results, langs, a.festival, a.years)
    else:
        text = "\n---\n\n".join(to_markdown(results, lang, a.festival, a.years) for lang in langs)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"Wrote {a.out}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
