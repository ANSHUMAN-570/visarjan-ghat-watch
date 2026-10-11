# Six-minute demo

Start: `streamlit run app.py`, browser at http://localhost:8501, language English, all filters at their defaults.

| Time | Say / show |
|---|---|
| **0:00-0:40 Problem** | "Three years of MPPCB ghat test results sit in 90-120 page PDFs. Durga Visarjan is on 20 October. An officer needs to know which ghats to look at first - and why." Point at the countdown banner and the tagline. |
| **0:40-1:30 Evidence** | **Overview** tab. "7 ghats, 1,524 observations, 2023-2025, from the MPPCB reports as extracted by the organisers." Show the cards (counts and sample sizes). Open **Check against the participant guide**: the guide says 42 of 116 DO and 100 of 112 BOD readings fail; "we recalculated them from the records and they match". Show **Data coverage** and the warnings: Bairagarh and Malikhedi have no Durga 2025 table; the Rani Kamlapati name mapping needs review. |
| **1:30-3:00 Ranking** | **Priority ranking** tab. Read the blue explanation box: weights are illustrative, not official, not a health measure. Show the table with counts beside rates; sort by a column. Open "How one site's score was computed" for Bairagarh: weights, rates, contributions. Tick Durga only in the sidebar and show the order change. |
| **3:00-4:00 Trust** | **Evidence explorer**. In the sidebar add the parameter **Lead** (BDL occurs only for heavy metals), then search `BDL`: qualifiers stay as printed, never zero. Pick Bairagarh: rows behind its score, with report file and page; click the PDF link (opens the report; the link carries the page number). Show a "not sampled" row in "Rows that could not be scored" - missing is not clean. To show the honest empty case: in the sidebar keep only Bairagarh + Shahpura, festival Durga, year 2025 - Bairagarh has no Durga 2025 table, so the ranking shows "Insufficient evidence - retest" with no score. |
| **4:00-5:00 Action brief** | **Historical comparison**: DO chart, dots not joined, benchmark line. Then **Action brief**: choose 3 sites, download the PDF, open it: English page, Hindi page, citations, warnings, follow-ups, screening-tool statement. Switch the sidebar to हिन्दी to show the Hindi interface. |
| **5:00-6:00 Impact** | "The officer gets a defensible shortlist for fresh sampling before 20 October, and every number traces back to a report page. It is a screening aid built on old data - it points to where to look first; official testing decides." State the limits: historical, units assumed, no coliform, no live data. |

Only features that exist in this repo are demonstrated. The optional AI summary and a map were **not** built.
