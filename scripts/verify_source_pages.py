"""Spot-check the page numbers in the readings file against the real MPPCB report PDFs.

    python scripts/verify_source_pages.py <folder-with-the-3-PDFs>

For every (site, year, festival, page) group it checks, on the cited page of that year's PDF:
  1. the page has extractable text,
  2. the printed site name (or a distinctive word of it) appears,
  3. what share of the reported results (numbers and BDL/ND qualifiers) of the group appear as tokens on the page.
A group "passes" when 1 and 2 hold and share >= 0.9. This is a consistency check, not proof of every digit:
numbers can coincide by chance, so ambiguous cases still need a human look at the page.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.data_loader import load_dataset  # noqa: E402


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z]+|\d+(?:\.\d+)?", text))


def main(folder: str) -> int:
    df, _, cfg = load_dataset()
    docs: dict[int, pymupdf.Document] = {}
    for year, src in cfg["sources"].items():
        p = Path(folder) / src["file"]
        if p.exists():
            docs[year] = pymupdf.open(p)
    print("PDFs opened:", {y: len(d) for y, d in docs.items()})
    results = []
    for (site, year, fest, page), g in df.dropna(subset=["source_page"]).groupby(
            ["site", "year", "festival", "source_page"], observed=True):
        doc = docs.get(int(year))
        if doc is None or not 1 <= int(page) <= len(doc):
            results.append((site, year, fest, page, "no pdf/page", 0.0))
            continue
        text = doc[int(page) - 1].get_text()
        if len(text.strip()) < 50:
            results.append((site, year, fest, page, "no text on page", 0.0))
            continue
        low = text.lower()
        printed = g["site_original"].iloc[0].lower()
        words = [w for w in re.findall(r"[a-z]{5,}", printed) if w not in ("bhopal", "visarjan", "visarjankund")]
        site_ok = any(w in low for w in words) or any(w in low for w in re.findall(r"[a-z]{5,}", site.lower()))
        toks = tokens(text)
        wanted = [r for r in g["reported_result"] if r and r not in ("_", "-", "*", "**")]
        share = sum(r in toks or r.rstrip("0").rstrip(".") in toks for r in wanted) / len(wanted) if wanted else 1.0
        results.append((site, year, fest, page, "ok" if site_ok else "site name not found", share))
    n = len(results)
    passed = [r for r in results if r[4] == "ok" and r[5] >= 0.9]
    print(f"groups checked: {n}; passed: {len(passed)}")
    for r in results:
        if r not in passed:
            print("  REVIEW:", r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
