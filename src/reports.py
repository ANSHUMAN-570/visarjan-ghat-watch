"""Decision brief (Hindi + English) and CSV exports. Everything here is derived from the ranking and evidence frames
that the dashboard shows, so exports and screen always agree."""
from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import pandas as pd

from .data_loader import KEY_PARAMETERS
from .evidence import coverage_gaps, key_findings, observation_rows
from .i18n import T
from .metrics import overview
from .ranking import INSUFFICIENT, SCORED

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


def _pct(cfg: dict, p: str) -> str:
    return f"{cfg['weights'][p] * 100:g}"


def _cell(rank_row: pd.Series, short: str) -> str:
    return f"{int(rank_row[f'{short}_n_beyond'])}/{int(rank_row[f'{short}_n_valid'])}"


def brief_model(df: pd.DataFrame, rank_df: pd.DataFrame, cfg: dict, lang: str, top_n: int = 3,
                prepared: date | None = None, scope: str | None = None) -> dict:
    """Plain-data description of one language's brief (used for Markdown and PDF)."""
    t = T[lang]
    prepared = prepared or date.today()
    ov = overview(df, cfg)
    years = ", ".join(str(y) for y in ov["years"]) or "-"
    scope_txt = t["b_scope_all"] if not scope else t["b_scope"].format(s=scope)
    weights = {"do": _pct(cfg, "Dissolved oxygen"), "bod": _pct(cfg, "BOD"), "ph": _pct(cfg, "pH")}

    scored = rank_df[rank_df["ranking_status"] == SCORED].head(top_n)
    insufficient = rank_df[rank_df["ranking_status"] == INSUFFICIENT]
    shorts = [cfg["benchmark"]["parameters"][p]["short"] for p in KEY_PARAMETERS]

    rows = [[str(int(r["rank"])), r["site"], f"{r['score']:.0f}"] + [_cell(r, s) for s in shorts]
            for _, r in scored.iterrows()]

    findings = []
    for _, r in scored.iterrows():
        lines = []
        for f in key_findings(df, cfg, r["site"], lang):
            p = t["param"][f["parameter"]]
            if f["n_valid"] == 0:
                lines.append(t["b_no_valid"].format(p=p))
            elif f["worst"] is None:
                lines.append(t["b_none_beyond"].format(p=p, b=f["n_beyond"], n=f["n_valid"]))
            else:
                w = f["worst"]
                lines.append(t["b_worst"].format(
                    p=p, b=f["n_beyond"], n=f["n_valid"], v=w["value"], year=w["year"],
                    fest=t["festival"].get(w["festival"], w["festival"]), phase=t["phase"].get(w["phase"], w["phase"]),
                    cite=w["citation"]))
        findings.append((f"{int(r['rank'])}. {r['site']}", lines))

    warnings = [t["b_w_insuff"].format(site=s) for s in insufficient["site"]]
    if ov["n_unscorable_key"]:
        warnings.append(t["b_w_unscored"].format(n=ov["n_unscorable_key"]))
    gaps = coverage_gaps(df)
    for site, missing in gaps.items():
        for year, fest in missing:
            warnings.append(t["b_w_gap"].format(site=site, year=year, festival=t["festival"].get(fest, fest)))
    review = sorted(df.loc[df["review_flag"], "site"].unique())
    if review:
        warnings.append(t["b_w_review"].format(sites=", ".join(review)))
    warnings += [t["b_w_old"], t["b_w_units"]]

    retest = sorted(set(insufficient["site"]) | set(gaps) | set(
        rank_df.loc[rank_df["params_without_data"].map(bool), "site"]))
    actions = [t["b_a1"]]
    if len(scored):
        actions.append(t["b_a2"].format(sites=", ".join(scored["site"])))
    actions.append(t["b_a3"].format(sites=", ".join(retest)) if retest else t["b_a3_none"])
    actions.append(t["b_a4"])

    return {
        "lang": lang, "title": t["b_title"], "prepared": f"{t['b_prepared']}: {prepared.strftime('%d %b %Y')}",
        "data": t["b_data"].format(years=years, sites=ov["n_sites"], n=ov["n_rows"], scope=scope_txt),
        "priority_title": t["b_priority"], "priority_header": t["b_cols"], "priority_rows": rows,
        "findings_title": t["b_findings"], "findings": findings,
        "warnings_title": t["b_warnings"], "warnings": warnings,
        "actions_title": t["b_actions"], "actions": actions,
        "disclaimer": t["b_disclaimer"].format(**weights),
    }


def brief_markdown(models: list[dict]) -> str:
    out = []
    for m in models:
        out += [f"# {m['title']}", "", m["prepared"], "", m["data"], "", f"## {m['priority_title']}", "",
                "| " + " | ".join(m["priority_header"]) + " |", "|" + "---|" * len(m["priority_header"])]
        out += ["| " + " | ".join(r) + " |" for r in m["priority_rows"]]
        out += ["", f"## {m['findings_title']}", ""]
        for head, lines in m["findings"]:
            out += [f"**{head}**", ""] + [f"- {x}" for x in lines] + [""]
        out += [f"## {m['warnings_title']}", ""] + [f"- {x}" for x in m["warnings"]]
        out += ["", f"## {m['actions_title']}", ""] + [f"- {x}" for x in m["actions"]]
        out += ["", f"_{m['disclaimer']}_", "", "---", ""]
    return "\n".join(out)


def ranking_csv(rank_df: pd.DataFrame, lang: str = "en") -> str:
    """Ranking table exactly as computed: counts beside every rate, no invented zero for unscored sites."""
    t = T[lang]
    d = rank_df.copy()
    d["ranking_status"] = d["ranking_status"].map({SCORED: "scored", INSUFFICIENT: "Insufficient evidence - retest"})
    d["years"] = d["years"].map(lambda ys: ";".join(str(y) for y in ys))
    d["weights_used"] = d["weights_used"].map(lambda w: ";".join(f"{k}={v:.3f}" for k, v in w.items()))
    d["params_without_data"] = d["params_without_data"].map(";".join)
    return d.to_csv(index=False, float_format="%.4f")


def evidence_csv(df: pd.DataFrame, cfg: dict, sites: list[str] | None = None, lang: str = "en") -> str:
    obs = observation_rows(df if sites is None else df[df["site"].isin(sites)], cfg, lang)
    return obs.to_csv(index=False)


# ---- PDF -----------------------------------------------------------------------------------------------------
def brief_pdf(models: list[dict]) -> bytes:
    """Bilingual PDF using bundled Noto fonts with text shaping so Devanagari conjuncts render correctly."""
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF(format="A4")
    pdf.set_margins(14, 14, 14)
    pdf.set_auto_page_break(True, 14)
    pdf.add_font("Latin", "", str(FONT_DIR / "NotoSans-Regular.ttf"))
    pdf.add_font("Latin", "B", str(FONT_DIR / "NotoSans-Bold.ttf"))
    pdf.add_font("Deva", "", str(FONT_DIR / "NotoSansDevanagari-Regular.ttf"))
    pdf.add_font("Deva", "B", str(FONT_DIR / "NotoSansDevanagari-Bold.ttf"))
    pdf.set_text_shaping(True)

    def line(text, size=10, bold=False, gap=1.5):
        pdf.set_font(base, "B" if bold else "", size)
        pdf.multi_cell(0, size * 0.52, text, align="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(gap)

    for m in models:
        base = "Deva" if m["lang"] == "hi" else "Latin"
        pdf.add_page()
        pdf.set_fallback_fonts(["Latin"] if base == "Deva" else ["Deva"], exact_match=False)
        line(m["title"], 17, True, 2)
        line(m["prepared"], 9, gap=2)
        line(m["data"], 9.5, gap=3)
        line(m["priority_title"], 13, True)
        widths = (14, 74, 20, 24, 24, 22)
        pdf.set_font(base, "B", 9)
        with pdf.table(col_widths=widths, text_align=("CENTER", "LEFT", "CENTER", "CENTER", "CENTER", "CENTER"),
                       line_height=6.5) as table:
            hdr = table.row()
            for h in m["priority_header"]:
                hdr.cell(h)
            pdf.set_font(base, "", 9)
            for r in m["priority_rows"]:
                row = table.row()
                for c in r:
                    row.cell(c)
        pdf.ln(3)
        line(m["findings_title"], 13, True)
        for head, lines in m["findings"]:
            line(head, 10.5, True, 0.5)
            for x in lines:
                line("•  " + x, 9.5, gap=0.8)
            pdf.ln(1.5)
        line(m["warnings_title"], 13, True)
        for x in m["warnings"]:
            line("•  " + x, 9.5, gap=0.8)
        pdf.ln(2)
        line(m["actions_title"], 13, True)
        for x in m["actions"]:
            line("•  " + x, 9.5, gap=0.8)
        pdf.ln(2)
        pdf.set_font(base, "", 9)
        line(m["disclaimer"], 9, gap=0)
    buf = pdf.output()
    return bytes(buf)
