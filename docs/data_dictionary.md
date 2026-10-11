# Data dictionary and canonical schema

## Inputs (`data/raw/`)

| File | Rows | Origin |
|---|---|---|
| `bhopal_ghats_2023_2025.csv` | 1,524 | Hackathon organisers' extraction of the MPPCB Ganesh/Durga visarjan reports for the 7 Bhopal ghats. **The dataset this app uses.** |
| `sample_bhopal_2025.csv` | 453 | The 2025 rows of the file above (not loaded by the app). |
| `cpcb_water_quality_criteria.csv` | 19 | CPCB water-quality classes A-E (reference; the benchmarks actually applied live in `config/thresholds.yaml`). |
| `DATA_DICTIONARY.md` | - | The organisers' original data dictionary (kept unchanged). |

Raw columns required by the loader: `year, festival, site, water_body, phase, parameter, value, unit_assumed, flag,
value_as_printed, site_as_printed, site_match_confidence, source_page`. A missing column stops the load with an error that
names it (`DataValidationError`); the app shows the message.

## Canonical schema (what every module works with)

| Column | Meaning |
|---|---|
| `site` | Standardised site name (the organisers' mapping). |
| `site_original` | Site name **exactly as printed** in the report. |
| `water_body` | Lake / kund the ghat is on. |
| `site_match_confidence` / `review_flag` | Organisers' confidence in the name mapping. `review_flag` is true unless confidence is `high`. |
| `year`, `festival`, `phase` | Report year; `Ganesh` or `Durga`; `pre` / `during` / `after` immersion. **No calendar dates exist in the data.** |
| `parameter` | One of 13 parameters. Only `Dissolved oxygen`, `BOD`, `pH` are benchmarked. |
| `value` | Number, or empty when the report shows no number. **Never filled.** |
| `unit` | Unit assumed by the organisers (the reports print none). |
| `status` | See below. |
| `qualifier` | The report's code (`BDL`, `ND`, `not sampled`, `*`, `**`), preserved verbatim. |
| `reported_result` | Exactly what the report shows (`value_as_printed`). |
| `source_file`, `source_url` | Report PDF for that year (mapping in `config/thresholds.yaml` -> `sources`). |
| `source_page` | PDF page in that report, from the organisers' file. Empty = "Source page not verified". |

Derived (never stored as a measurement): `benchmark` = `within` / `beyond` / `not_scored`; `counts_toward_score`.

## Status values

| `status` | Meaning | Scored? |
|---|---|---|
| `measured` | A number was reported. | Yes (if the parameter has a benchmark) |
| `bdl` | Below detection limit. Kept as BDL; not zero. | No |
| `nd` | Not detected. Distinct from BDL; not zero. | No |
| `not_sampled` | `not sampled`, `*`, `**`. Missing, not clean. | No |
| `missing` | Blank / `_` / `-`. Missing, not clean. | No |
| `invalid` | Printed text that is neither a number nor a known code, or an impossible number (pH outside 0-14, negative DO/BOD). Kept and reported. | No |
| `invalid_unit` | A benchmarked parameter whose unit does not match the benchmark unit. Kept and reported. | No |

BDL/ND are not given an interpretation: the reports give no detection limits we could verify, so treating BDL as zero (or any
value) would be an assumption. In the real data BDL occurs only for heavy metals, which have no Class B benchmark.

## Benchmarks (`config/thresholds.yaml`)

| Parameter | Benchmark used | Source |
|---|---|---|
| Dissolved oxygen | at least 5 mg/L | CPCB Class B (outdoor bathing, organised), as stated in the Track 2 participant guide |
| BOD | at most 3 mg/L | same |
| pH | 6.5 to 8.5, inclusive | same |

These are bathing-water (Class B) benchmarks, not limits for every water use. Total coliform (<= 500 MPN/100 ml for Class B) is
**not in the dataset**, so it is not scored.

## Ranking formula

`score = 100 * sum(w_p * violation_rate_p) / sum(w_p)` over parameters with at least one valid reading, with illustrative
weights DO 0.40, BOD 0.40, pH 0.20 (`weights:` in the config). Parameters without a valid reading are dropped and the others
renormalised; they are never counted as zero violations. A site with fewer than `min_valid_readings_per_site` valid readings
is "Insufficient evidence - retest" and gets no score.

## Provenance and trust

* Participant-guide figures (42 of 116 DO, 100 of 112 BOD, four zero DO readings at Bairagarh) are kept in the config as
  *reported* and shown beside our recalculation (Overview tab). They are never used as results.
* The organisers spot-checked 6 tables against the PDF text. We ran `scripts/verify_source_pages.py` against the three real
  PDFs: all 40 (site, year, festival, page) groups passed (site name found on the cited page and at least 90% of the printed
  results present as tokens on it). This is a consistency check, not a digit-by-digit audit.
