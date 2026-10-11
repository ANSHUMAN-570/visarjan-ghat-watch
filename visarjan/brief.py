"""One-page officer brief (HTML, print-to-PDF ready) and Markdown, in English and/or Hindi."""
from __future__ import annotations

from html import escape

from .i18n import UI, render_reason
from .scoring import GhatResult

MAX_REASONS = 4
_TIER_COLOR = {"high": "#b42318", "medium": "#b54708", "low": "#067647"}


def _scope(lang: str, festival: str | None, years: list[int] | None) -> str:
    ui = UI[lang]
    fest = ui["festival"].get(festival, festival) if festival else ui["scope_all"]
    yrs = ", ".join(str(y) for y in sorted(years)) if years else "2023-2025"
    return f"{fest}; {ui['years']}: {yrs}"


def top_reasons(g: GhatResult) -> list[dict]:
    """Top findings, plus every data-gap warning: gaps must never be cut for length."""
    findings = [r for r in g.reasons if not r["type"].startswith("gap_")]
    gaps = [r for r in g.reasons if r["type"].startswith("gap_")]
    return findings[:MAX_REASONS] + gaps


def to_markdown(results: list[GhatResult], lang: str, festival: str | None = None,
                years: list[int] | None = None) -> str:
    ui = UI[lang]
    lines = [f"# {ui['brief_title']}", "", f"**{ui['scope']}:** {_scope(lang, festival, years)}", "",
             f"| {ui['rank']} | {ui['ghat']} | {ui['risk']} | {ui['score']} | {ui['confidence']} |", "|---|---|---|---|---|"]
    for g in results:
        conf = ui["conf_low"] if g.low_confidence else ui["conf_ok"]
        lines.append(f"| {g.rank} | {g.site} | {ui['tier'][g.tier]} | {g.score:.0f} | {conf} |")
    for g in results:
        lines += ["", f"## {g.rank}. {g.site} ({g.water_body}) - {ui['tier'][g.tier]}, {g.score:.0f}/100", ""]
        lines += [f"- {render_reason(r, lang)}" for r in top_reasons(g)]
        lines += ["", f"**{ui['actions']}:**"] + [f"- {ui['action'][a]}" for a in g.actions]
    lines += ["", f"**{ui['limits_title']}:** {ui['limits']}", "", f"**{ui['method_title']}:** {ui['method']}", "",
              f"**{ui['limitations_title']}**", ""] + [f"- {x}" for x in ui["limitations"]]
    lines += ["", f"_{ui['generated']}: MPPCB Ganesh/Durga visarjan reports 2023-2025 (see data/DATA_DICTIONARY.md)._"]
    return "\n".join(lines) + "\n"


def _section_html(results: list[GhatResult], lang: str, festival: str | None, years: list[int] | None) -> str:
    ui = UI[lang]
    e = escape
    rows = []
    for g in results:
        conf = ui["conf_low"] if g.low_confidence else ui["conf_ok"]
        rows.append(
            f"<tr><td>{g.rank}</td><td>{e(g.site)}</td>"
            f"<td style='color:{_TIER_COLOR[g.tier]};font-weight:700'>{e(ui['tier'][g.tier])}</td>"
            f"<td>{g.score:.0f}</td><td>{'&#9888; ' if g.low_confidence else ''}{e(conf)}</td></tr>")
    cards = []
    for g in results:
        reasons = "".join(f"<li>{e(render_reason(r, lang))}</li>" for r in top_reasons(g))
        actions = "".join(f"<li>{e(ui['action'][a])}</li>" for a in g.actions)
        cards.append(
            f"<div class='card'><h3>{g.rank}. {e(g.site)} <small>({e(g.water_body)})</small> "
            f"<span style='color:{_TIER_COLOR[g.tier]}'>{e(ui['tier'][g.tier])} &middot; {g.score:.0f}/100</span></h3>"
            f"<ul>{reasons}</ul><b>{e(ui['actions'])}</b><ul>{actions}</ul></div>")
    lim = "".join(f"<li>{e(x)}</li>" for x in ui["limitations"])
    return (
        f"<section lang='{lang}'><h1>{e(ui['brief_title'])}</h1>"
        f"<p><b>{e(ui['scope'])}:</b> {e(_scope(lang, festival, years))}</p>"
        f"<table><tr><th>{e(ui['rank'])}</th><th>{e(ui['ghat'])}</th><th>{e(ui['risk'])}</th>"
        f"<th>{e(ui['score'])}</th><th>{e(ui['confidence'])}</th></tr>{''.join(rows)}</table>"
        f"{''.join(cards)}"
        f"<p><b>{e(ui['limits_title'])}:</b> {e(ui['limits'])}</p>"
        f"<p><b>{e(ui['method_title'])}:</b> {e(ui['method'])}</p>"
        f"<p><b>{e(ui['limitations_title'])}</b></p><ul>{lim}</ul>"
        f"<p class='src'>{e(ui['generated'])}: MPPCB Ganesh/Durga visarjan reports 2023-2025.</p></section>")


_CSS = """
body{font-family:'Noto Sans Devanagari','Nirmala UI','Segoe UI',Arial,sans-serif;margin:24px;color:#101828;font-size:13px}
h1{font-size:20px;margin:0 0 6px}h3{font-size:14px;margin:0 0 4px}small{font-weight:400;color:#475467}
table{border-collapse:collapse;width:100%;margin:8px 0}th,td{border:1px solid #d0d5dd;padding:4px 8px;text-align:left}
th{background:#f2f4f7}.card{border:1px solid #d0d5dd;border-radius:6px;padding:8px 12px;margin:8px 0;break-inside:avoid}
ul{margin:4px 0 6px 18px;padding:0}.src{color:#475467;font-size:11px}section{page-break-after:always}
@media print{body{margin:10mm}}
"""


def to_html(results: list[GhatResult], langs: tuple[str, ...] = ("en", "hi"), festival: str | None = None,
            years: list[int] | None = None) -> str:
    body = "".join(_section_html(results, lang, festival, years) for lang in langs)
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{escape(UI['en']['title'])}</title>"
            f"<style>{_CSS}</style></head><body>{body}</body></html>")
