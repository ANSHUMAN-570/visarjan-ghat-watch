import io

import pandas as pd
import pymupdf
import pytest

from src.data_loader import load_dataset
from src.evidence import citation, coverage_gaps, key_findings, observation_rows, site_detail, wide_view
from src.ranking import rank_sites
from src.reports import brief_markdown, brief_model, brief_pdf, evidence_csv, ranking_csv

from .fixtures import CFG, canonical, row, site_rows

REAL, _ISSUES, REAL_CFG = load_dataset()


# ---- evidence / source references ------------------------------------------------------------------------
def test_citation_has_file_and_page_or_says_unverified():
    assert citation("report.pdf", 12) == "report.pdf, p.12"
    assert "Source page not verified" in citation("report.pdf", None)
    assert "सत्यापित नहीं" in citation("report.pdf", float("nan"), "hi")


def test_every_real_observation_row_has_file_page_and_original_site_name():
    obs = observation_rows(REAL, REAL_CFG)
    assert len(obs) == 1524
    assert obs["source_file"].notna().all() and obs["source_page"].notna().all()
    assert obs["site_original"].str.len().gt(0).all()
    assert obs["citation"].str.contains(r"\.pdf, p\.\d+").all()


def test_counts_toward_score_matches_benchmark_and_excludes_qualifiers():
    df = canonical(site_rows("SYNTHETIC A", do=["4", "BDL", "ND", "not sampled", "6"], bod=["2"], ph=["7"]))
    obs = observation_rows(df, CFG)
    do = obs[obs["parameter"] == "Dissolved oxygen"]
    assert do["counts_toward_score"].sum() == 2
    assert set(do.loc[~do["counts_toward_score"], "qualifier"]) == {"BDL", "ND", "not sampled"}


def test_summary_counts_equal_displayed_evidence_rows():
    ranked = rank_sites(REAL, REAL_CFG)
    for _, r in ranked.iterrows():
        det = site_detail(REAL, REAL_CFG, r["site"])["contributing"]
        assert len(det) == r["n_valid"]
        assert (det["benchmark"] == "beyond").sum() == r["DO_n_beyond"] + r["BOD_n_beyond"] + r["pH_n_beyond"]


def test_key_findings_report_worst_reading_with_citation():
    df = canonical([row("SYNTHETIC A", "Dissolved oxygen", "4.5", phase="pre", page="11"),
                    row("SYNTHETIC A", "Dissolved oxygen", "1.5", phase="during", page="12"),
                    row("SYNTHETIC A", "Dissolved oxygen", "7", phase="after", page="13")])
    do = key_findings(df, CFG, "SYNTHETIC A")[0]
    assert (do["n_valid"], do["n_beyond"]) == (3, 2)
    assert do["worst"]["value"] == 1.5 and do["worst"]["citation"].endswith("p.12")


def test_wide_view_keeps_qualifiers_as_printed():
    df = canonical(site_rows("SYNTHETIC A", do=["4", "BDL"], bod=["2", "2"], ph=["7", "7"]))
    w = wide_view(df, CFG)
    assert "BDL –" in set(w["Dissolved oxygen"])


def test_coverage_gaps_find_missing_festival_tables():
    df = canonical(site_rows("SYNTHETIC A", do=["4"] * 3, bod=["5"] * 3, ph=["7"] * 3, year=2025) +
                   site_rows("SYNTHETIC B", do=["4"] * 3, bod=["5"] * 3, ph=["7"] * 3, year=2024))
    gaps = coverage_gaps(df)
    assert gaps["SYNTHETIC A"] == [(2024, "Durga")] and gaps["SYNTHETIC B"] == [(2025, "Durga")]
    g = coverage_gaps(REAL)
    assert any(s.startswith("Bairagarh") for s in g) and any(s.startswith("Malikhedi") for s in g)


# ---- exports and brief -----------------------------------------------------------------------------------
def test_ranking_csv_leaves_unscored_site_blank_and_labelled_not_zero():
    rows = site_rows("SYNTHETIC GOOD", do=["7"] * 3, bod=["1"] * 3, ph=["7"] * 3) + \
        site_rows("SYNTHETIC EMPTY", do=[""] * 3, bod=[""] * 3, ph=[""] * 3)
    csv = pd.read_csv(io.StringIO(ranking_csv(rank_sites(canonical(rows), CFG))))
    empty = csv[csv["site"] == "SYNTHETIC EMPTY"].iloc[0]
    assert pd.isna(empty["score"]) and empty["ranking_status"] == "Insufficient evidence - retest"


def test_exports_agree_with_the_ranking():
    ranked = rank_sites(REAL, REAL_CFG)
    csv = pd.read_csv(io.StringIO(ranking_csv(ranked)))
    assert list(csv["site"]) == list(ranked["site"])
    assert csv["score"].round(2).tolist() == ranked["score"].round(2).tolist()
    ev = pd.read_csv(io.StringIO(evidence_csv(REAL, REAL_CFG)))
    assert len(ev) == 1524 and ev["counts_toward_score"].sum() == ranked["n_valid"].sum()


def test_brief_model_contents_and_honest_wording():
    ranked = rank_sites(REAL, REAL_CFG)
    for lang in ("en", "hi"):
        m = brief_model(REAL, ranked, REAL_CFG, lang, top_n=3)
        assert len(m["priority_rows"]) == 3 and m["priority_rows"][0][1].startswith("Bairagarh")
        assert any("p." in line and ".pdf" in line for _, lines in m["findings"] for line in lines)
        assert m["warnings"] and m["actions"] and m["disclaimer"]
    en = brief_model(REAL, ranked, REAL_CFG, "en")
    text = " ".join(en["warnings"] + en["actions"] + [en["disclaimer"]]).lower()
    assert "screening tool" in text and "20 october 2026" in text
    assert "safe" not in " ".join(en["warnings"]).replace("not a finding that the site is safe", "").lower()


def test_brief_flags_insufficient_site_and_never_calls_it_safe():
    rows = site_rows("SYNTHETIC GOOD", do=["7"] * 3, bod=["1"] * 3, ph=["7"] * 3) + \
        site_rows("SYNTHETIC EMPTY", do=[""] * 3, bod=[""] * 3, ph=[""] * 3)
    df = canonical(rows)
    m = brief_model(df, rank_sites(df, CFG), CFG, "en")
    assert any("SYNTHETIC EMPTY" in w and "insufficient evidence" in w for w in m["warnings"])
    assert any("SYNTHETIC EMPTY" in a for a in m["actions"] if "Retest" in a)


def test_markdown_brief_contains_both_languages():
    ranked = rank_sites(REAL, REAL_CFG)
    md = brief_markdown([brief_model(REAL, ranked, REAL_CFG, lg) for lg in ("en", "hi")])
    assert "Ghat water-quality review brief" in md and "घाट जल-गुणवत्ता समीक्षा संक्षेप" in md


def test_pdf_is_valid_bilingual_and_devanagari_text_is_present():
    ranked = rank_sites(REAL, REAL_CFG)
    pdf = brief_pdf([brief_model(REAL, ranked, REAL_CFG, lg) for lg in ("en", "hi")])
    assert pdf[:4] == b"%PDF"
    doc = pymupdf.open(stream=pdf, filetype="pdf")
    text = "".join(p.get_text() for p in doc)
    assert "Ghat water-quality review brief" in text and "Bairagarh" in text
    assert "समीक्षा" in text and "स्थल" in text
    assert "�" not in text  # no replacement characters (broken glyph mapping)
    fonts = {f[3] for p in doc for f in p.get_fonts()}
    assert any("Devanagari" in f for f in fonts)


def test_everything_works_without_any_api_key(monkeypatch):
    for k in ("CEREBRAS_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    ranked = rank_sites(REAL, REAL_CFG)
    assert brief_pdf([brief_model(REAL, ranked, REAL_CFG, "en")])[:4] == b"%PDF"
