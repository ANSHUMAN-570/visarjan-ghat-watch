"""Visarjan Ghat Watch: one page for the BMC officer. What to send where, before Durga visarjan."""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from visarjan.brief import to_html, top_reasons
from visarjan.data import KEY_PARAMS, load_limits, load_readings
from visarjan.i18n import APP, LANGS, UI, render_reason
from visarjan.scoring import score_ghats
from visarjan.summary import latest_check

VISARJAN = date(2026, 10, 20)
ICON = {"high": "🔴", "medium": "🟠", "low": "🟢"}
LIMIT_TEXT = {"pH": "6.5–8.5", "Dissolved oxygen": "≥ 5 mg/l", "BOD": "≤ 3 mg/l"}
MARK = {"ok": "✅", "violation": "❌", "missing": "⬜"}

st.set_page_config(page_title="Visarjan Ghat Watch", page_icon="🌊", layout="centered")


@st.cache_data
def _load():
    return load_readings(), load_limits()


readings, limits = _load()

lang = st.radio("Language / भाषा", list(LANGS), format_func=LANGS.get, horizontal=True, label_visibility="collapsed")
ui, app = UI[lang], APP[lang]

st.title(f"🌊 {ui['title']}")
left = (VISARJAN - date.today()).days
if left > 0:
    st.error(app["days_left"].format(n=left), icon="⏳")
elif left == 0:
    st.error(app["days_today"], icon="⏳")
st.write(app["tagline"])

with_ganesh = st.checkbox(app["incl_ganesh"], value=False)
results = score_ghats(readings, limits, None if with_ganesh else "Durga")

# ---- 1. work list: what to dispatch where ---------------------------------------------------
st.header(app["dispatch_title"])
cols = st.columns(3)
for col, action in zip(cols, ("clean", "aerate", "retest")):
    with col, st.container(border=True):
        st.markdown(f"**{app['list'][action]}**")
        names = [f"{g.rank}. {g.site.split(' (')[0].split(' /')[0]}" + (" ⚠️" if g.low_confidence and action == "retest" else "")
                 for g in results if action in g.actions]
        st.markdown("\n".join(f"- {n}" for n in names) if names else f"_{app['none']}_")
st.caption("⚠️ = " + app["gap_mark"])

st.download_button(f"⬇️ {app['download']}",
                   to_html(results, ("en", "hi"), None if with_ganesh else "Durga"),
                   "visarjan_brief.html", "text/html", type="primary")

# ---- 2. ranked ghats ------------------------------------------------------------------------
st.header(app["ranking_title"])
for g in results:
    with st.container(border=True):
        head, badge = st.columns([3, 1])
        head.markdown(f"### {g.rank}. {g.site}")
        head.caption(g.water_body)
        badge.markdown(f"### {ICON[g.tier]} {ui['tier'][g.tier]}")
        badge.caption(f"{ui['score']}: {g.score:.0f}/100")

        for r in top_reasons(g):
            st.markdown(f"- {render_reason(r, lang)}")
        st.markdown("**" + ui["actions"] + ":** " + " · ".join(ui["action"][a].rstrip(".।") for a in g.actions))

        # latest Durga test vs the limits: the figures the officer can quote
        year, table = latest_check(readings, limits, g.site, "Durga")
        fest_name = ui["festival"]["Durga"]
        if year is None:
            st.info(app["latest_none"].format(festival=fest_name))
        else:
            st.markdown(f"**{app['latest_title'].format(festival=fest_name, year=year)}**")
            df = pd.DataFrame({
                app["col_param"]: [ui["param"][p] for p in table],
                app["limit_row"]: [LIMIT_TEXT[p] for p in table],
                **{ui["phase"][ph]: [f"{MARK[table[p][ph][1]]} {table[p][ph][0]}" for p in table]
                   for ph in ("pre", "during", "after")},
            })
            st.dataframe(df, hide_index=True, width="stretch")

        with st.expander(app["all_readings"]):
            raw = readings[(readings["site"] == g.site) & readings["parameter"].isin(KEY_PARAMS)
                           & ((readings["festival"] == "Durga") | with_ganesh)].sort_values(
                ["year", "festival", "parameter", "phase"])
            out = pd.DataFrame({
                app["col_param"]: raw["parameter"].map(ui["param"]),
                app["col_year"]: raw["year"],
                app["col_festival"]: raw["festival"].map(ui["festival"]),
                app["col_phase"]: raw["phase"].astype(str).map(ui["phase"]),
                app["col_value"]: raw["value_as_printed"].fillna("-"),
                app["col_state"]: raw["status"].map(app["state"]),
                app["col_page"]: raw["source_page"],
            })
            st.dataframe(out, hide_index=True, width="stretch")

st.divider()
st.caption(app["footer"])
