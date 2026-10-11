# Data

* `raw/` - inputs as received. `bhopal_ghats_2023_2025.csv` is the dataset the app loads (extracted by the hackathon
  organisers from the MPPCB reports; see `raw/DATA_DICTIONARY.md`).
* `processed/` - reproducible outputs of `python scripts/build_processed.py`: `observations_canonical.csv` (every row with
  original text, status, benchmark result and citation) and `validation_report.txt`.

## Source reports (not stored in this repo)

| Year | File | URL |
|---|---|---|
| 2025 | Ganesh_and_Durga_visarjan_report-2025.pdf | https://www.mppcb.mp.gov.in/proc/mon/Ganesh_and_Durga_visarjan_report-2025.pdf |
| 2024 | Ganesh_and_Durga_visarjan_report-2024.pdf | https://www.mppcb.mp.gov.in/proc/mon/Ganesh_and_Durga_visarjan_report-2024.pdf |
| 2023 | Idol_immer._Report_23_CPCB.pdf | https://www.mppcb.mp.gov.in/proc/mon/Idol_immer._Report_23_CPCB.pdf |

Links are from the organisers' data dictionary, which lists them as downloaded on 10 Oct 2026; we fetched all three on 11 Oct 2026
to run the page check. Not included here: the statewide immersion-site file (`mp_immersion_sites_2023_2025.csv`), which the
organisers describe as less checked; only the 7 Bhopal ghats are used.

## Adding real data

1. Put a CSV with the **same columns** as `raw/bhopal_ghats_2023_2025.csv` in `raw/` (required columns are listed in
   `docs/data_dictionary.md`). Keep `value` empty and put the report's code (`BDL`, `ND`, `not sampled`) in `flag`; never type 0
   for a qualifier.
2. Add the report file name and URL for any new year under `sources:` in `config/thresholds.yaml`.
3. Point `DEFAULT_DATA` in `src/data_loader.py` at the new file (or call `load_dataset(path)`), then run
   `python scripts/build_processed.py` and read `processed/validation_report.txt`.
4. Run `python scripts/verify_source_pages.py <folder-with-PDFs>` to check page citations.

If you add made-up or test rows, name the sites `SYNTHETIC ...` as the tests do, so they cannot be mistaken for MPPCB results.
