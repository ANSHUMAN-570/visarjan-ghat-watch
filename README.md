# Visarjan Ghat Watch

Decision-support dashboard for Bhopal Municipal Corporation (BMC) officers. It turns three years of MPPCB ghat water-test
results (2023-2025) into a traceable priority list, so officers can decide **where to review and retest first before Durga
Visarjan on 20 October 2026**. Built for the Bhopal Impact Lab 2026, Track 2.

**Team:** [TEAM NAME] - [member 1], [member 2], [member 3], [member 4] *(fill in before submitting)*

> **Historical data only.** The readings are MPPCB test results from 2023-2025. They do not describe conditions on 20 October
> 2026, the app has no live government data, and it is a screening aid - not a substitute for official testing or municipal
> judgement. It is not an official BMC or MPPCB product.

## The problem
The MPPCB results sit in 90-120 page PDFs. Nobody compares them against the bathing-water benchmarks, across ghats or across
years. The officer needs: which ghats to look at first, why, and exactly which readings (and report pages) support that.

## Features
* **Overview** - counts computed from the loaded data (sites, observations, DO / BOD / pH benchmark exceedances with sample
  sizes, results that cannot be scored), a recalculation of the participant guide's reported figures, data coverage and gaps.
* **Priority ranking** - sortable table; transparent score with counts beside every rate; "how this score was computed" per site;
  *Insufficient evidence - retest* instead of a made-up score.
* **Evidence explorer** - every observation with original site name, report as printed, qualifier, unit, source file, **source
  page** (with a link to the PDF at that page), mapping confidence; searchable and filterable; rows behind each site's score.
* **Historical comparison** - readings against the benchmark line (dots are not joined into fake trends), valid/violation counts,
  year coverage.
* **Action brief** - bilingual (English + Hindi) decision brief as **PDF** (bundled Devanagari font, rendering checked), Markdown
  and CSV; ranking and evidence CSVs.
* English / Hindi interface, filters by site, year, festival, parameter and observation status.

Screenshots: `docs/screenshots/`.

## Run it (5 steps)
Python 3.10+ (developed on 3.12).
```bash
git clone <this-repo-url> && cd visarjan-ghat-watch      # 1. get the code
python -m venv .venv && source .venv/bin/activate        # 2. virtual environment (Windows: .venv\Scripts\activate)
pip install -r requirements.txt                          # 3. install
streamlit run app.py                                     # 4. open http://localhost:8501
python -m pytest -q                                      # 5. optional: run the tests
```
No API key or internet connection is needed.

## Landing page (`site/`)
A static, dependency-free landing page (HTML, CSS, vanilla JS) that presents the project and links to the dashboard.
```bash
python -m http.server 8000 -d site      # open http://localhost:8000 (keep `streamlit run app.py` running for the dashboard links)
```
* Sections: hero, numbered features 01-08 (only implemented features; AI summary, map and data upload are labelled
  **Upcoming**), how it works, benefits, about, FAQ, final call to action, footer.
* Dark/light mode: follows the device setting on first visit, remembers the choice in `localStorage`, set before first paint.
* The dashboard URL is set once in `<meta name="dashboard-url">` in `site/index.html`. It points to the hosted dashboard
  (https://anshuman-570-visarjan-ghat-watch-app-mmpnpx.streamlit.app/); change it to `http://localhost:8501` to test against a local dashboard.

### Deploying the landing page to Vercel
`vercel.json` (repo root) serves `site/` as a static site: framework preset "Other", no install, no build, clean URLs,
security headers (including a Content-Security-Policy) and a 7-day cache for `site/assets/`.

1. Push the repo to GitHub, then in Vercel choose **Add New → Project** and import it. Leave **Root Directory** as the repo
   root; `vercel.json` sets everything else. (CLI alternative: `npx vercel` from the repo root, then `npx vercel --prod`.)
2. **Point the buttons at a hosted dashboard.** Vercel hosts only the landing page - it cannot run the Streamlit app, which
   needs a long-running Python server. Deploy `app.py` somewhere that runs Streamlit (for example Streamlit Community Cloud),
   then put that URL in `<meta name="dashboard-url">` in `site/index.html`. The dashboard is hosted on Streamlit Community
   Cloud (main file `app.py`, Python 3.12) and redeploys automatically when `main` is pushed.
3. If you edit the inline `<script>` in the `<head>` of `site/index.html`, run `python scripts/update_csp_hash.py` so the
   Content-Security-Policy still allows it.

## Project structure
```
app.py                       Streamlit dashboard (5 tabs, EN/HI)
src/data_loader.py           config + CSV -> canonical, traceable table
src/data_validation.py       schema checks, status classification (BDL/ND/not sampled), units, plausibility
src/metrics.py               benchmark comparison, per-site/parameter statistics, guide-figure check
src/ranking.py               transparent weighted violation-rate score
src/evidence.py              citations, evidence rows, per-site detail, coverage gaps
src/reports.py               bilingual brief (PDF, Markdown) and CSV exports
src/i18n.py                  English and Hindi text
config/thresholds.yaml       benchmarks, ILLUSTRATIVE weights, scoring rules, report-file mapping
data/raw/, data/processed/   inputs and reproducible outputs (see data/README.md)
docs/data_dictionary.md      schema, status codes, benchmarks, provenance
scripts/                     verify_source_pages.py (page check against the PDFs), build_processed.py
tests/                       pytest suite (synthetic fixtures are named "SYNTHETIC ...")
assets/fonts/                Noto Sans + Noto Sans Devanagari (SIL OFL) for the PDF
site/                        static landing page (index.html, styles.css, app.js, assets/ screenshots)
```

## Data
Source: MPPCB Ganesh/Durga visarjan reports 2023-2025, as extracted by the hackathon organisers
(`data/raw/bhopal_ghats_2023_2025.csv`, 1,524 readings, 7 ghats, 13 parameters). Report links and how to add real data:
[`data/README.md`](data/README.md). Schema and status codes: [`docs/data_dictionary.md`](docs/data_dictionary.md).

**Benchmarks** (from the participant guide; CPCB **Class B, outdoor bathing** - not limits for every water use):
DO at least 5 mg/L, BOD at most 3 mg/L, pH 6.5-8.5 inclusive. Coliform is not in the dataset and is not scored.

## Ranking formula - illustrative, not official
`score = 100 x sum(w_p x violation_rate_p) / sum(w_p)` over DO, BOD and pH, where `violation_rate_p` is the share of **valid
numeric** readings outside the benchmark. Weights: DO 40%, BOD 40%, pH 20% (`config/thresholds.yaml`).

* The weights are an **illustrative project choice**, not MPPCB/CPCB weights and not a validated health-risk formula. The score is
  not a probability of illness, a concentration or a legal category.
* If a parameter has no valid reading it is **dropped and the other weights are renormalised**; it is never counted as zero violations.
* A site with fewer than `min_valid_readings_per_site` (default 1) valid readings is shown as **"Insufficient evidence - retest"**
  with no score. Counts are shown beside every rate; parameters with fewer than 3 valid readings are flagged "low sample".
* Ties are broken by site name, so the ranking is deterministic.

## Missing-data policy
Blank and "not sampled" (`*`, `**`) are **missing, not clean**. `BDL` and `ND` are kept as separate qualifiers, never converted to
zero and never scored (no verifiable detection limits). Units are validated against the benchmark; mismatches, unreadable text
and impossible numbers (pH 40, negative BOD) are kept, flagged and excluded. Nothing is imputed. Original site names and source
files/pages are preserved; an absent page is shown as "Source page not verified".

## Validation done
* `python -m pytest -q`: benchmarks incl. boundary values, missing/BDL/ND, units, ranking maths and renormalisation, determinism,
  evidence citations, exports agreeing with the ranking, PDF validity and Devanagari text, no API key needed.
* The guide's figures (42/116 DO, 100/112 BOD, four zero DO readings at Bairagarh in 2023 and 2025) **were recalculated from the
  loaded data and match** (Overview tab).
* `python scripts/verify_source_pages.py <pdf-folder>` against the real PDFs: 40 of 40 table groups found on the cited page.
  This is a consistency check, not a digit-by-digit audit.
* The Hindi PDF was rendered and inspected visually (conjuncts and matras correct). A native Hindi reader should still review the
  wording in `src/i18n.py`.

## Known limitations
* Historical 2023-2025 data; **no calendar dates** in the dataset (only year, festival, phase).
* Units are assumed (the reports print none). Only DO, BOD and pH are benchmarked; metals and others are shown but not scored.
* Bairagarh and Malikhedi have **no Durga 2025 table** in the data (flagged). "Rani Kamlapati ghat / Kamla Park kund" may be two
  places (medium mapping confidence). Page numbers come from the organisers' file (we spot-checked them, see above).
* No map (no verified coordinates). No prediction. The optional Cerebras AI summary was **not implemented**; the app is fully
  deterministic.
* Not deployed anywhere; runs locally.

## Six-minute demo
See [`docs/DEMO.md`](docs/DEMO.md).

## License
MIT (see `LICENSE`). Fonts: SIL Open Font License (see `assets/fonts/README.md`). Data: from the hackathon organisers; reports
are MPPCB publications.
