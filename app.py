"""Streamlit app: ranked ghat list, traceable readings, downloadable Hindi/English brief."""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from visarjan.brief import to_html, to_markdown
from visarjan.data import KEY_PARAMS, PHASE_ORDER, load_limits, load_readings
from visarjan.i18n import LANGS, UI, render_reason
from visarjan.scoring import score_ghats

st.set_page_config(page_title="Visarjan Ghat Watch", page_icon="🌊", layout="wide")


@st.cache_data
def _load():
    return load_readings(), load_limits()


readings, limits = _load()

with st.sidebar:
    lang = st.radio("Language / भाषा", list(LANGS), format_func=LANGS.get, horizontal=True)
    ui = UI[lang]
    fest_opts = [None, "Durga", "Ganesh"]
    festival = st.selectbox(
        ui["scope"], fest_opts,
        format_func=lambda f: ui["scope_all"] if f is None else ui["festival"][f])
    all_years = sorted(readings["year"].unique().tolist())
    years = st.multiselect(ui["years"], all_years, default=all_years)

st.title(f"🌊 {ui['title']}")
st.caption(ui["subtitle"])

results = score_ghats(readings, limits, festival, years or None)
if not results:
    st.warning(ui["no_data"])
    st.stop()

# ---- ranking -------------------------------------------------------------------------------
icon = {"high": "🔴", "medium": "🟠", "low": "🟢"}
table = pd.DataFrame([{
    ui["rank"]: g.rank,
    ui["ghat"]: g.site,
    ui["water_body"]: g.water_body,
    ui["risk"]: f"{icon[g.tier]} {ui['tier'][g.tier]}",
    ui["score"]: g.score,
    ui["confidence"]: ("⚠️ " + ui["conf_low"]) if g.low_confidence else ui["conf_ok"],
    ui["actions"]: " / ".join(ui["action"][a].rstrip(".।") for a in g.actions),
} for g in results])
st.dataframe(
    table, hide_index=True, width="stretch",
    column_config={ui["score"]: st.column_config.ProgressColumn(
        ui["score"], min_value=0, max_value=100, format="%.0f")})

# ---- brief downloads -----------------------------------------------------------------------
c1, c2, c3 = st.columns(3)
c1.download_button("⬇️ Brief (हिन्दी + English, HTML → print/PDF)",
                   to_html(results, ("en", "hi"), festival, years or None),
                   "visarjan_brief.html", "text/html")
c2.download_button("⬇️ English (Markdown)", to_markdown(results, "en", festival, years or None),
                   "visarjan_brief_en.md", "text/markdown")
c3.download_button("⬇️ हिन्दी (Markdown)", to_markdown(results, "hi", festival, years or None),
                   "visarjan_brief_hi.md", "text/markdown")

# ---- ghat detail ---------------------------------------------------------------------------
st.divider()
by_name = {g.site: g for g in results}
site = st.selectbox(ui["ghat"], list(by_name))
g = by_name[site]
st.subheader(f"{icon[g.tier]} {g.site} - {ui['tier'][g.tier]} ({g.score:.0f}/100)")
left, right = st.columns([1, 1])
with left:
    st.markdown(f"**{ui['why']}**")
    for r in g.reasons:
        st.markdown(f"- {render_reason(r, lang)}")
with right:
    st.markdown(f"**{ui['actions']}**")
    for a in g.actions:
        st.markdown(f"- {ui['action'][a]}")
    st.caption(f"{ui['confidence']}: {g.coverage:.0%} "
               f"({g.n_expected_readings - g.n_missing_readings}/{g.n_expected_readings})")

site_df = readings[(readings["site"] == site) & readings["parameter"].isin(KEY_PARAMS)].copy()
if festival:
    site_df = site_df[site_df["festival"] == festival]
if years:
    site_df = site_df[site_df["year"].isin(years)]
site_df["when"] = (site_df["year"].astype(str) + " " + site_df["festival"] + " "
                   + site_df["phase"].astype(str))
order = [f"{y} {f} {p}" for y in sorted(site_df["year"].unique()) for f in ("Ganesh", "Durga")
         for p in PHASE_ORDER if f"{y} {f} {p}" in set(site_df["when"])]

param = st.selectbox("Parameter", KEY_PARAMS, format_func=lambda p: ui["param"][p])
pdf = site_df[(site_df["parameter"] == param) & (site_df["status"] == "value")]
lim = limits[param]
base = alt.Chart(pdf).encode(
    x=alt.X("when:N", sort=order, title=None, axis=alt.Axis(labelAngle=-60)),
    y=alt.Y("value:Q", title=f"{ui['param'][param]}"),
    tooltip=["when", "value", "source_page"])
layers = [base.mark_line(color="#667085", opacity=0.4, point=False),
          base.mark_point(size=80, filled=True, color="#175cd3")]
for v in (lim.lo, lim.hi):
    if v is not None:
        layers.append(alt.Chart(pd.DataFrame({"limit": [v]})).mark_rule(color="#b42318", strokeDash=[6, 4])
                      .encode(y="limit:Q"))
st.altair_chart(alt.layer(*layers), width="stretch")
st.caption("Red dashed line = CPCB Class B limit. Gaps in the line are missing readings (never plotted as zero).")

st.markdown("**Raw readings behind every number**")
raw = site_df[site_df["parameter"] == param][
    ["year", "festival", "phase", "value", "value_as_printed", "status", "source_page"]]
st.dataframe(raw.sort_values(["year", "festival", "phase"]), hide_index=True, width="stretch")

# ---- honesty -------------------------------------------------------------------------------
with st.expander(ui["limitations_title"], expanded=False):
    for x in ui["limitations"]:
        st.markdown(f"- {x}")
    st.markdown(f"**{ui['limits_title']}:** {ui['limits']}")
    st.markdown(f"**{ui['method_title']}:** {ui['method']}")
