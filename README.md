# Visarjan Ghat Watch

Bhopal Impact Lab 2026, Track 2. Turns three years of MPPCB ghat water tests into a ranked risk list and a one-page
Hindi + English brief **before Durga visarjan (20 Oct 2026)**.

**Team:** [TEAM NAME] — [member 1], [member 2], [member 3], [member 4]  *(fill in before submitting)*

## The one user
A **BMC officer planning Durga visarjan**. They need to decide which ghats get cleaning, aeration or a fresh water
test first. This tool gives them a ranked list of the 7 Bhopal ghats, a plain-language reason for each, the exact
readings (with report page) behind every number, and a printable brief.

## Run it (5 steps)
```bash
git clone <this-repo-url> && cd visarjan-ghat-watch     # 1. get the code
pip install -r requirements.txt                          # 2. Python 3.10+
streamlit run app.py                                     # 3. open the app (language toggle: English / हिन्दी)
python -m visarjan.cli --festival Durga --lang both --out brief.html   # 4. or write the brief directly
python -m pytest -q                                      # 5. check the numbers (27 tests)
```
Open `brief.html` in a browser and print to PDF. A sample is in `examples/brief_durga.html`.

### JavaScript front end (static page, no framework)
```bash
python -m visarjan.export                 # scores in Python -> web/data.json + printable briefs
python -m http.server -d web 8000         # open http://localhost:8000
```
`web/` is plain HTML/CSS/JS (`index.html`, `app.js`, `style.css`) that renders `data.json`; it has no build step and can be
hosted on GitHub Pages. All scoring stays in Python, so both front ends show identical numbers. Re-run the export after
changing data or scoring.

## How the ranking works
Compared against **CPCB Class B (outdoor bathing)** limits read from `data/cpcb_water_quality_criteria.csv`:
pH 6.5–8.5, dissolved oxygen ≥ 5 mg/l, BOD ≤ 3 mg/l.

Score 0–100 = **50%** share of readings beyond a limit + **30%** how far beyond + **20%** share of
before/during/after test series where oxygen fell or BOD rose by ≥ 1 mg/l after immersion began. The first two parts
blend the average and the worst of the three parameters, so one clean parameter cannot hide a failing one. Newer
years weigh more. Tiers: **High ≥ 65**, **Medium ≥ 45**, else Low. Every constant is at the top of
`visarjan/scoring.py`.

Every claim in the app links back to rows in the data: parameter, year, festival, phase and the **report page**.

## Missing data, handled honestly
| In the data | Treated as |
|---|---|
| `BDL`, `ND` | very low (not zero, not missing). Counts as within a *maximum* limit (BOD), as a failure for a *minimum* limit (oxygen) |
| `not sampled`, `*`, `**`, blank, `_` | **missing — never counted as clean**, never plotted as zero |
| A whole festival table absent for a ghat | flagged "data gap"; confidence marked LOW; action "take a fresh sample" |

Example: Bairagarh and Malikhedi have **no Durga 2025 table**, so they are flagged as low-confidence rather than
looking cleaner than they are.

## What works / what doesn't
**Works:** ranking for all/Durga/Ganesh and any year selection; traceable reasons; Hindi + English brief (template
based, no AI/LLM, works offline); source page for every reading; tests against the figures in the problem statement
(42 of 116 oxygen readings < 5; 100 of 112 BOD readings > 3; Bairagarh oxygen = 0 four times).

**Doesn't / limits:**
- Only 2023–2025 MPPCB reports. No live or current readings.
- The reports print no units. Standard units are assumed (as in the data dictionary).
- Only pH, oxygen and BOD have Class B limits in this dataset. Coliform (limit 500 MPN/100 ml) is **not in the data**.
  Heavy metals have no Class B limit, so they are not scored.
- Tier thresholds and weights are judgement calls, not an official standard. The score ranks ghats against each
  other; it is **not a health or safety certificate** and makes no health claims.
- "Worse after immersion began" is an observation, not proof of cause.
- "Rani Kamlapati ghat / Kamla Park kund" may be two places (match confidence: medium).
- The statewide file (`mp_immersion_sites_2023_2025.csv`, less checked) is not used; only the 7 Bhopal ghats are scored.

## Layout
```
app.py                  Streamlit app: one page, work list + ranked ghats
web/                    static JS front end (index.html, app.js, style.css, data.json)
visarjan/export.py      writes web/data.json and briefs
visarjan/data.py        loading, missing-data rules, CPCB limits
visarjan/scoring.py     scoring, tiers, actions, coverage
visarjan/brief.py       HTML / Markdown brief       visarjan/i18n.py   English + Hindi text
visarjan/cli.py         command-line brief      visarjan/summary.py  latest Durga test vs limits
tests/                  pytest
data/                   organisers' CSVs (see data/DATA_DICTIONARY.md)
```

## Data and credits
Data and problem statement from the Bhopal Impact Lab 2026 organisers
(https://github.com/Vishal4742/bhopal-impact-lab-2026-problem-statements, Track 2 `data/`). Original sources:
MPPCB Ganesh & Durga visarjan reports 2023–2025 (https://www.mppcb.mp.gov.in) and CPCB water quality criteria
(https://cpcb.gov.in/water-quality-criteria/). No API keys or personal data are used.

Licence: MIT (see `LICENSE`).
