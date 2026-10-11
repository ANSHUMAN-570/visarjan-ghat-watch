"""Visarjan Ghat Watch - decision-support dashboard for BMC officers (historical MPPCB data, 2023-2025).

Run:  streamlit run app.py
"""
from __future__ import annotations

import logging
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import KEY_PARAMETERS, load_dataset
from src.evidence import coverage_gaps, observation_rows, site_detail, wide_view
from src.i18n import LANGS, T
from src.metrics import guide_check, overview, with_benchmark
from src.ranking import INSUFFICIENT, SCORED, rank_sites
from src.reports import brief_markdown, brief_model, brief_pdf, evidence_csv, ranking_csv

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("visarjan")
log.setLevel(logging.INFO)

st.set_page_config(page_title="Visarjan Ghat Watch", page_icon="🌊", layout="wide")
st.markdown("""
<style>
.block-container{padding-top:1.4rem;max-width:1250px}
.vgw-card{background:#fff;border:1px solid #d0d5dd;border-radius:10px;padding:12px 14px;min-height:150px}
.vgw-card .lab{font-size:.8rem;color:#475467}
.vgw-card .val{font-size:1.9rem;font-weight:700;color:#101828;line-height:1.2}
.vgw-card .sub{font-size:.8rem;color:#475467}
.vgw-card.bad .val{color:#b42318}
.vgw-banner{background:#eff8ff;border:1px solid #b2ddff;color:#194185;border-radius:10px;padding:10px 14px;margin:6px 0 12px}
.vgw-foot{color:#475467;font-size:.8rem;border-top:1px solid #d0d5dd;margin-top:28px;padding-top:10px}
</style>""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _load():
    return load_dataset()


try:
    df_all, issues, cfg = _load()
except Exception as exc:  # show a readable error instead of a stack trace
    log.exception("data load failed")
    st.error(f"Could not load the data: {exc}")
    st.stop()

# ---- sidebar -------------------------------------------------------------------------------------------
with st.sidebar:
    lang = st.radio("Language / भाषा", list(LANGS), format_func=LANGS.get, horizontal=True)
    t = T[lang]
    st.subheader(t["sidebar_filters"])
    all_sites = sorted(df_all["site"].unique())
    sel_sites = st.multiselect(t["f_site"], all_sites, default=all_sites)
    all_years = sorted(int(y) for y in df_all["year"].dropna().unique())
    sel_years = st.multiselect(t["f_year"], all_years, default=all_years)
    all_fest = sorted(df_all["festival"].unique())
    sel_fest = st.multiselect(t["f_festival"], all_fest, default=all_fest, format_func=lambda f: t["festival"].get(f, f))
    st.caption("↓ " + {"en": "Applies to the explorer and charts only", "hi": "केवल प्रमाण-खोज और चार्ट पर लागू"}[lang])
    all_params = sorted(df_all["parameter"].unique(), key=lambda p: (p not in KEY_PARAMETERS, p))
    sel_params = st.multiselect(t["f_param"], all_params, default=KEY_PARAMETERS, format_func=lambda p: t["param"].get(p, p))
    all_status = [s for s in t["status"] if s in set(df_all["status"])]
    sel_status = st.multiselect(t["f_status"], all_status, default=all_status, format_func=t["status"].get)

df = df_all[df_all["site"].isin(sel_sites) & df_all["year"].isin(sel_years) & df_all["festival"].isin(sel_fest)]

st.title(f"🌊 {t['title']}")
days = (date.fromisoformat(str(cfg["visarjan_date"])) - date.today()).days
if days >= 0:
    st.markdown(f"<div class='vgw-banner'>⏳ <b>{t['days_today'] if days == 0 else t['days_left'].format(n=days)}</b></div>",
                unsafe_allow_html=True)
st.caption(t["subtitle"])

if df.empty:
    st.warning(t["empty"])
    st.stop()

ov = overview(df, cfg)
rank_df = rank_sites(df, cfg, sites=sel_sites)

tabs = st.tabs(t["tabs"])


def card(label: str, value: str, sub: str = "", bad: bool = False, help_: str = "") -> str:
    return (f"<div class='vgw-card{' bad' if bad else ''}' title='{help_}'><div class='lab'>{label}</div>"
            f"<div class='val'>{value}</div><div class='sub'>{sub}</div></div>")


def pct(x: float) -> str:
    return "–" if pd.isna(x) else f"{x * 100:.0f}%"


# ---- 1. overview ---------------------------------------------------------------------------------------
with tabs[0]:
    pp = ov["per_param"]
    cols = st.columns(6)
    cols[0].markdown(card(t["card_sites"], str(ov["n_sites"]), ", ".join(map(str, ov["years"]))), unsafe_allow_html=True)
    cols[1].markdown(card(t["card_obs"], f"{ov['n_rows']:,}", t["card_obs_help"]), unsafe_allow_html=True)
    for c, p, key, hlp in ((cols[2], "Dissolved oxygen", "card_do", "help_do"), (cols[3], "BOD", "card_bod", "help_bod"),
                           (cols[4], "pH", "card_ph", "help_ph")):
        c.markdown(card(t[key], f"{pp[p]['n_beyond']}", f"{pct(pp[p]['rate'])} · {t['of_valid'].format(n=pp[p]['n_valid'])}",
                        bad=True, help_=t[hlp]), unsafe_allow_html=True)
    cols[5].markdown(card(t["card_unscored"], str(ov["n_unscorable_key"]), f"/ {ov['n_key_rows']}", help_=t["card_unscored_help"]),
                     unsafe_allow_html=True)
    st.caption(t["benchmark_note"].format(label=cfg["benchmark"]["label"]))
    st.info(t["no_dates"])

    st.subheader(t["guide_title"])
    st.caption(t["guide_note"])
    gc = guide_check(df_all, cfg)
    gc["matches"] = gc["matches"].map({True: "✅", False: "❌"})
    gc.columns = t["guide_cols"]
    st.dataframe(gc, hide_index=True, width="stretch")

    left, right = st.columns(2)
    with left:
        st.subheader(t["qual_title"])
        q = (df["status"].map(t["status"]).value_counts().rename_axis("status").reset_index(name="n"))
        st.dataframe(q, hide_index=True, width="stretch")
        st.caption("BDL / ND / not sampled are kept as reported and are never turned into zero or counted as clean.")
    with right:
        st.subheader(t["coverage_title"])
        ob = with_benchmark(df[df["parameter"].isin(KEY_PARAMETERS)], cfg)
        cov = (ob[ob["benchmark"] != "not_scored"].pivot_table(index="site", columns="year", values="value",
                                                               aggfunc="size", fill_value=0))
        st.dataframe(cov, width="stretch")
        st.caption(t["hist_cov"])
    gaps = coverage_gaps(df)
    if gaps:
        st.subheader(t["gaps_title"])
        for site, missing in gaps.items():
            for year, fest in missing:
                st.warning(t["gap_line"].format(site=site, year=year, festival=t["festival"].get(fest, fest)))
    review = sorted(df.loc[df["review_flag"], "site"].unique())
    if review:
        st.warning(t["warn_review"].format(sites=", ".join(review)))
    with st.expander(t["validation_title"]):
        if not issues:
            st.success(t["validation_ok"])
        for i in issues:
            (st.error if i.severity == "error" else st.warning if i.severity == "warning" else st.info)(i.message)

# ---- 2. priority ranking -------------------------------------------------------------------------------
with tabs[1]:
    w = cfg["weights"]
    st.info(f"**{t['score_title']}**\n\n" + t["score_text"].format(
        do=f"{w['Dissolved oxygen'] * 100:g}", bod=f"{w['BOD'] * 100:g}", ph=f"{w['pH'] * 100:g}"))
    rc = t["rank_cols"]
    rows = []
    gaps_now = coverage_gaps(df)
    for _, r in rank_df.iterrows():
        notes = []
        if r["ranking_status"] == INSUFFICIENT:
            notes.append(t["insufficient"])
        if r["low_sample"]:
            notes.append(t["low_sample"])
        notes += [t["no_data_for"].format(p=t["param"][p]) for p in r["params_without_data"] if r["ranking_status"] == SCORED]
        notes += [t["gap_line"].format(site="", year=y, festival=t["festival"].get(f, f)).lstrip(": ")
                  for y, f in gaps_now.get(r["site"], [])]
        row = {rc["rank"]: None if pd.isna(r["rank"]) else int(r["rank"]), rc["site"]: r["site"],
               rc["score"]: r["score"]}
        for p in KEY_PARAMETERS:
            k = cfg["benchmark"]["parameters"][p]["short"]
            n = int(r[f"{k}_n_valid"])
            row[rc[k]] = f"{int(r[f'{k}_n_beyond'])}/{n} ({pct(r[f'{k}_rate'])})" if n else "–"
        row[rc["years"]] = ", ".join(map(str, r["years"])) or "–"
        row[rc["latest"]] = int(r["latest_year"]) if pd.notna(r["latest_year"]) else None
        row[rc["complete"]] = pct(r["completeness"])
        row[rc["note"]] = "; ".join(notes)
        rows.append(row)
    tbl = pd.DataFrame(rows)
    tbl[[rc["rank"], rc["latest"]]] = tbl[[rc["rank"], rc["latest"]]].astype("Int64")  # blank, not a text dash, for sites without a rank
    st.dataframe(tbl, hide_index=True, width="stretch",
                 column_config={rc["score"]: st.column_config.ProgressColumn(
                     rc["score"], min_value=0, max_value=100, format="%.0f",
                     help="0-100. Illustrative weighted violation rate; not a health-risk measure.")})
    st.caption({"en": "Click a column header to sort. Counts beside each rate are valid numeric readings only.",
                "hi": "क्रमबद्ध करने के लिए कॉलम शीर्षक पर क्लिक करें। हर दर के साथ की गिनती केवल मान्य संख्यात्मक रीडिंग की है।"}[lang])

    st.subheader({"en": "How one site's score was computed", "hi": "एक स्थल का स्कोर कैसे निकला"}[lang])
    pick = st.selectbox(t["select_site"], list(rank_df["site"]), key="rank_site")
    r = rank_df[rank_df["site"] == pick].iloc[0]
    if r["ranking_status"] == INSUFFICIENT:
        st.warning(t["insufficient"])
    else:
        cc = t["calc_cols"]
        calc = []
        for p in KEY_PARAMETERS:
            k = cfg["benchmark"]["parameters"][p]["short"]
            wu = r["weights_used"].get(p)
            calc.append({cc[0]: t["param"][p], cc[1]: f"{w[p] * 100:g}%",
                         cc[2]: "–" if wu is None else f"{wu * 100:.1f}%",
                         cc[3]: int(r[f"{k}_n_valid"]), cc[4]: int(r[f"{k}_n_beyond"]),
                         cc[5]: pct(r[f"{k}_rate"]),
                         cc[6]: "–" if wu is None else f"{100 * wu * r[f'{k}_rate']:.1f}"})
        st.dataframe(pd.DataFrame(calc), hide_index=True, width="stretch")
        st.caption(f"= {r['score']:.1f} / 100")

# ---- 3. evidence explorer ------------------------------------------------------------------------------
with tabs[2]:
    ev_df = df[df["parameter"].isin(sel_params) & df["status"].isin(sel_status)]
    obs = observation_rows(ev_df, cfg, lang)
    q = st.text_input(t["f_search"], "")
    if q:
        mask = obs.astype(str).apply(lambda col: col.str.contains(q, case=False, regex=False)).any(axis=1)
        obs = obs[mask]
    if obs.empty:
        st.warning(t["empty"])
    else:
        st.caption(t["verify_note"])
        url_by_file = df.drop_duplicates("source_file").set_index("source_file")["source_url"].to_dict()
        shown = obs.copy()
        shown["open_report"] = [
            f"{url_by_file.get(f)}#page={int(p)}" if f in url_by_file and pd.notna(p) else (url_by_file.get(f) or "")
            for f, p in zip(shown["source_file"], shown["source_page"])]
        shown["festival"] = shown["festival"].map(lambda f: t["festival"].get(f, f))
        shown["status"] = shown["status"].map(t["status"])
        shown["benchmark"] = shown["benchmark"].map(t["benchmark"])
        st.subheader(t["obs_table_title"] + f" — {len(shown):,}")
        st.dataframe(shown.drop(columns=["counts_toward_score"]), hide_index=True, width="stretch",
                     column_config={"open_report": st.column_config.LinkColumn(t["open_pdf"], display_text="PDF ↗"),
                                    "year": st.column_config.NumberColumn(format="%d"),
                                    "source_page": st.column_config.NumberColumn(format="%d")})
        st.download_button(t["download_obs"], evidence_csv(ev_df, cfg, lang=lang), "visarjan_evidence_rows.csv", "text/csv")

        st.subheader(t["wide_title"])
        st.dataframe(wide_view(df, cfg), hide_index=True, width="stretch")

    st.divider()
    site = st.selectbox(t["select_site"], sel_sites, key="ev_site")
    det = site_detail(df, cfg, site)
    if det["observations"].empty:
        st.warning(t["empty"])
    else:
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown(f"**{t['byyear_title']}**")
            by = det["by_year"].rename(columns={"valid": "valid", "beyond": "beyond"})
            by["parameter"] = by["parameter"].map(t["param"])
            st.dataframe(by, hide_index=True, width="stretch")
        with c2:
            st.markdown(f"**{t['contrib_title']}** — {len(det['contributing'])}")
            st.dataframe(det["contributing"][["year", "festival", "phase", "parameter", "reported_result", "benchmark", "citation"]],
                         hide_index=True, width="stretch")
        if len(det["not_scored"]):
            st.markdown(f"**{t['notscored_title']}** — {len(det['not_scored'])}")
            st.dataframe(det["not_scored"][["year", "festival", "phase", "parameter", "reported_result", "qualifier", "status", "citation"]],
                         hide_index=True, width="stretch")

# ---- 4. historical comparison --------------------------------------------------------------------------
with tabs[3]:
    st.subheader(t["hist_title"])
    st.caption(t["hist_note"])
    p_sel = st.selectbox(t["f_param"], KEY_PARAMETERS, format_func=lambda p: t["param"][p], key="hist_param")
    h = with_benchmark(df[(df["parameter"] == p_sel)], cfg)
    pts = h[h["status"] == "measured"].copy()
    b = cfg["benchmark"]["parameters"][p_sel]
    if pts.empty:
        st.warning(t["empty"])
    else:
        pts["year"] = pts["year"].astype(int).astype(str)
        pts["phase_label"] = pts["phase"].astype(str).map(t["phase"])
        pts["festival_label"] = pts["festival"].map(t["festival"])
        pts["benchmark_label"] = pts["benchmark"].map(t["benchmark"])
        from src.evidence import citation
        pts["source"] = [citation(f, pg, lang) for f, pg in zip(pts["source_file"], pts["source_page"])]
        fig = px.strip(pts, x="site", y="value", color="year", stripmode="group",
                       category_orders={"year": [str(y) for y in sorted(int(x) for x in pts["year"].unique())]},
                       hover_data={"festival_label": True, "phase_label": True, "benchmark_label": True, "source": True,
                                   "year": False, "site": False},
                       labels={"value": f"{t['param'][p_sel]} ({b['unit'] or 'pH units'})", "site": t["axis_site"]})
        fig.update_traces(marker={"size": 9, "opacity": 0.85})
        lines = [b["value"]] if b["rule"] in ("min", "max") else [b["min"], b["max"]]
        for v in lines:
            fig.add_hline(y=v, line_dash="dash", line_color="#b42318", annotation_text=f"{b['display']}",
                          annotation_position="top left")
        fig.update_layout(height=480, margin={"t": 30, "b": 10}, legend_title_text=t["f_year"])
        st.plotly_chart(fig, width="stretch")
        n_np = int(((h["status"] != "measured")).sum())
        if n_np:
            st.caption({"en": f"{n_np} results for this parameter are not plotted (blank, not sampled, BDL, ND or invalid).",
                        "hi": f"इस पैरामीटर के {n_np} परिणाम चार्ट में नहीं हैं (खाली, नमूना नहीं लिया, BDL, ND या अमान्य)।"}[lang])

    st.subheader(t["hist_counts"])
    cnt = with_benchmark(df[df["parameter"].isin(KEY_PARAMETERS)], cfg)
    cnt = cnt[cnt["benchmark"] != "not_scored"].groupby(["parameter", "site", "benchmark"]).size().reset_index(name="n")
    if cnt.empty:
        st.warning(t["empty"])
    else:
        cnt["parameter"] = cnt["parameter"].map(t["param"])
        cnt["benchmark"] = cnt["benchmark"].map(t["benchmark"])
        fig2 = px.bar(cnt, x="n", y="site", color="benchmark", facet_col="parameter", orientation="h",
                      color_discrete_map={t["benchmark"]["within"]: "#2e7d6b", t["benchmark"]["beyond"]: "#b42318"},
                      labels={"n": t["axis_count"], "site": t["axis_site"], "benchmark": ""})
        fig2.update_layout(height=420, margin={"t": 30}, legend={"orientation": "h", "y": -0.2})
        fig2.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        st.plotly_chart(fig2, width="stretch")

# ---- 5. action brief -----------------------------------------------------------------------------------
with tabs[4]:
    st.subheader(t["brief_title"])
    st.caption(t["brief_intro"])
    top_n = st.slider(t["brief_top"], 1, max(1, len(rank_df)), min(3, max(1, len(rank_df))))
    narrowed = []
    if len(sel_sites) < len(all_sites):
        narrowed.append(f"{t['f_site']}: {', '.join(sel_sites)}")
    if len(sel_years) < len(all_years):
        narrowed.append(f"{t['f_year']}: {', '.join(map(str, sel_years))}")
    if len(sel_fest) < len(all_fest):
        narrowed.append(f"{t['f_festival']}: {', '.join(t['festival'].get(f, f) for f in sel_fest)}")
    scope = "; ".join(narrowed) or None
    models = [brief_model(df, rank_df, cfg, lg, top_n, date.today(), scope) for lg in ("en", "hi")]
    md = brief_markdown(models)
    d1, d2, d3, d4 = st.columns(4)
    try:
        d1.download_button(t["dl_pdf"], brief_pdf(models), "visarjan_brief.pdf", "application/pdf", type="primary")
    except Exception as exc:
        log.exception("pdf generation failed")
        d1.warning(t["pdf_fail"].format(e=exc))
    d2.download_button(t["dl_md"], md, "visarjan_brief.md", "text/markdown")
    d3.download_button(t["dl_csv_rank"], ranking_csv(rank_df, lang), "visarjan_ranking.csv", "text/csv")
    d4.download_button(t["dl_csv_obs"], evidence_csv(df, cfg, list(rank_df.loc[rank_df['ranking_status'] == SCORED, 'site'].head(top_n)) or None, lang),
                       "visarjan_brief_evidence.csv", "text/csv")
    with st.expander({"en": "Preview (English)", "hi": "पूर्वावलोकन (English)"}[lang], expanded=True):
        st.markdown(brief_markdown(models[:1]))
    with st.expander({"en": "Preview (हिन्दी)", "hi": "पूर्वावलोकन (हिन्दी)"}[lang]):
        st.markdown(brief_markdown(models[1:]))

st.markdown(f"<div class='vgw-foot'>{t['footer']}</div>", unsafe_allow_html=True)
