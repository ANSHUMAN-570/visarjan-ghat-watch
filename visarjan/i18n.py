"""English / Hindi text. Briefs are template-generated, so they work offline and never invent facts."""
from __future__ import annotations

from .scoring import TIER_HIGH, TIER_MEDIUM

LANGS = {"en": "English", "hi": "हिन्दी"}

UI = {
    "en": {
        "title": "Visarjan Ghat Watch",
        "subtitle": "Water-quality risk ranking of Bhopal immersion ghats, for the BMC officer planning Durga visarjan",
        "brief_title": "Ghat risk brief for visarjan planning",
        "scope": "Scope",
        "scope_all": "all festivals",
        "years": "years",
        "rank": "Rank", "ghat": "Ghat", "water_body": "Water body", "risk": "Risk", "score": "Score",
        "confidence": "Data confidence", "actions": "Actions", "why": "Why",
        "conf_ok": "OK", "conf_low": "LOW - data gap",
        "tier": {"high": "HIGH", "medium": "MEDIUM", "low": "LOW"},
        "param": {"pH": "pH", "Dissolved oxygen": "Dissolved oxygen (DO)", "BOD": "BOD"},
        "festival": {"Ganesh": "Ganesh", "Durga": "Durga"},
        "phase": {"pre": "before", "during": "during", "after": "after"},
        "action": {
            "clean": "Arrange cleaning / organic-waste removal before immersion.",
            "aerate": "Arrange aeration and re-check dissolved oxygen.",
            "retest": "Take a fresh water sample before immersion.",
            "monitor": "Routine monitoring.",
        },
        "limits_title": "Limits used (CPCB Class B, outdoor bathing)",
        "limits": "pH 6.5-8.5 | Dissolved oxygen at least 5 mg/l | BOD at most 3 mg/l",
        "limitations_title": "What this brief cannot tell you",
        "limitations": [
            "Based only on MPPCB reports for 2023-2025. No live or current readings.",
            "Reports print no units; standard units are assumed (mg/l for oxygen and BOD).",
            "Only pH, dissolved oxygen and BOD have Class B limits in this data. Coliform is not in the dataset.",
            "Missing or 'not sampled' readings are shown as missing. They are never counted as clean.",
            "The score ranks ghats against each other to prioritise action. It is not a health or safety certificate.",
            "'Rani Kamlapati ghat / Kamla Park kund' may be two different places (match confidence: medium).",
        ],
        "method_title": "How the score works",
        "method": "Score 0-100 = 50% share of readings beyond a limit + 30% how far beyond (each blends the average and the worst of pH/oxygen/BOD) + 20% share of tests where "
                  "oxygen fell or BOD rose by 1 mg/l or more during/after immersion. Newer years weigh more. "
                  f"High >= {TIER_HIGH:g}, Medium >= {TIER_MEDIUM:g}.",
        "source": "Source",
        "page": "report p.",
        "generated": "Generated from",
        "no_data": "No data for this selection.",
    },
    "hi": {
        "title": "विसर्जन घाट वॉच",
        "subtitle": "दुर्गा विसर्जन की योजना बनाने वाले BMC अधिकारी के लिए भोपाल के विसर्जन घाटों की जल-गुणवत्ता जोखिम रैंकिंग",
        "brief_title": "विसर्जन योजना के लिए घाट जोखिम संक्षिप्त रिपोर्ट",
        "scope": "दायरा",
        "scope_all": "सभी त्योहार",
        "years": "वर्ष",
        "rank": "क्रम", "ghat": "घाट", "water_body": "जल स्रोत", "risk": "जोखिम", "score": "स्कोर",
        "confidence": "डेटा की विश्वसनीयता", "actions": "कार्रवाई", "why": "कारण",
        "conf_ok": "ठीक", "conf_low": "कम - डेटा अधूरा",
        "tier": {"high": "उच्च", "medium": "मध्यम", "low": "कम"},
        "param": {"pH": "pH", "Dissolved oxygen": "घुलित ऑक्सीजन (DO)", "BOD": "BOD"},
        "festival": {"Ganesh": "गणेश", "Durga": "दुर्गा"},
        "phase": {"pre": "पहले", "during": "दौरान", "after": "बाद में"},
        "action": {
            "clean": "विसर्जन से पहले सफ़ाई / जैविक कचरा हटाने की व्यवस्था करें।",
            "aerate": "वायुकरण (एरेशन) की व्यवस्था करें और घुलित ऑक्सीजन दोबारा जाँचें।",
            "retest": "विसर्जन से पहले पानी का नया नमूना लेकर जाँच कराएँ।",
            "monitor": "नियमित निगरानी।",
        },
        "limits_title": "प्रयुक्त मानक (CPCB श्रेणी B, खुले में स्नान)",
        "limits": "pH 6.5-8.5 | घुलित ऑक्सीजन कम से कम 5 mg/l | BOD अधिकतम 3 mg/l",
        "limitations_title": "यह रिपोर्ट क्या नहीं बता सकती",
        "limitations": [
            "यह केवल 2023-2025 की MPPCB रिपोर्टों पर आधारित है। कोई ताज़ा या लाइव रीडिंग नहीं है।",
            "रिपोर्टों में इकाइयाँ नहीं छपी हैं; मानक इकाइयाँ मानी गई हैं (ऑक्सीजन और BOD के लिए mg/l)।",
            "इस डेटा में केवल pH, घुलित ऑक्सीजन और BOD के लिए श्रेणी B मानक हैं। कोलीफ़ॉर्म डेटा में नहीं है।",
            "अनुपलब्ध या 'नमूना नहीं लिया' रीडिंग को अनुपलब्ध ही दिखाया गया है; उन्हें कभी साफ़ नहीं माना गया।",
            "स्कोर घाटों की आपस में तुलना कर कार्रवाई की प्राथमिकता तय करने के लिए है। यह स्वास्थ्य या सुरक्षा प्रमाणपत्र नहीं है।",
            "'रानी कमलापति घाट / कमला पार्क कुंड' दो अलग स्थान हो सकते हैं (मिलान विश्वसनीयता: मध्यम)।",
        ],
        "method_title": "स्कोर कैसे बनता है",
        "method": "स्कोर 0-100 = 50% मानक से बाहर रीडिंग का अनुपात + 30% मानक से कितनी दूर + 20% वे जाँचें जिनमें "
                  "विसर्जन के दौरान/बाद ऑक्सीजन 1 mg/l या अधिक घटी या BOD 1 mg/l या अधिक बढ़ा। नए वर्षों को अधिक महत्व। "
                  f"उच्च >= {TIER_HIGH:g}, मध्यम >= {TIER_MEDIUM:g}।",
        "source": "स्रोत",
        "page": "रिपोर्ट पृ.",
        "generated": "आधार",
        "no_data": "इस चयन के लिए कोई डेटा नहीं।",
    },
}

_REASON = {
    "en": {
        "zero_do": "Dissolved oxygen read 0 mg/l {n} time(s) (limit: at least 5).",
        "do_low": "Dissolved oxygen below 5 mg/l in {v} of {n} readings; lowest {worst} mg/l ({where}).",
        "bod_high": "BOD above 3 mg/l in {v} of {n} readings; highest {worst} mg/l ({where}).",
        "ph_out": "pH outside 6.5-8.5 in {v} of {n} readings; most extreme {worst} ({where}).",
        "worse_during": "In {v} of {n} before/during/after tests, oxygen was lower or BOD higher after immersion began "
                        "(an observation, not proof of cause).",
        "gap_event": "No {festival} {year} test table in the report - the latest data for this ghat is older.",
        "gap_missing": "{n} of {total} key readings are missing or not sampled. They are NOT counted as clean.",
        "where": "{year} {festival}, {phase}, report p.{page}",
    },
    "hi": {
        "zero_do": "घुलित ऑक्सीजन {n} बार 0 mg/l दर्ज हुई (मानक: कम से कम 5)।",
        "do_low": "{n} में से {v} रीडिंग में घुलित ऑक्सीजन 5 mg/l से कम; न्यूनतम {worst} mg/l ({where})।",
        "bod_high": "{n} में से {v} रीडिंग में BOD 3 mg/l से अधिक; अधिकतम {worst} mg/l ({where})।",
        "ph_out": "{n} में से {v} रीडिंग में pH 6.5-8.5 से बाहर; सबसे अधिक विचलन {worst} ({where})।",
        "worse_during": "{n} में से {v} पहले/दौरान/बाद की जाँचों में विसर्जन शुरू होने के बाद ऑक्सीजन कम या BOD अधिक रहा "
                        "(यह अवलोकन है, कारण का प्रमाण नहीं)।",
        "gap_event": "रिपोर्ट में {year} की {festival} जाँच तालिका नहीं है - इस घाट का नवीनतम डेटा पुराना है।",
        "gap_missing": "{total} में से {n} मुख्य रीडिंग उपलब्ध नहीं / नमूना नहीं लिया गया। इन्हें साफ़ नहीं माना गया है।",
        "where": "{year} {festival}, {phase}, रिपोर्ट पृ. {page}",
    },
}


def _num(x: float | None) -> str:
    return "?" if x is None else f"{x:g}"


def render_reason(r: dict, lang: str) -> str:
    t, ui = _REASON[lang], UI[lang]
    kind = r["type"]
    if kind in ("do_low", "bod_high", "ph_out"):
        where = t["where"].format(
            year=r["year"], festival=ui["festival"].get(r["festival"], r["festival"]),
            phase=ui["phase"].get(r["phase"], r["phase"]), page=r["page"] if r["page"] is not None else "?")
        return t[kind].format(v=r["v"], n=r["n"], worst=_num(r["worst"]), where=where)
    if kind == "gap_event":
        return t[kind].format(year=r["year"], festival=ui["festival"].get(r["festival"], r["festival"]))
    return t[kind].format(**{k: v for k, v in r.items() if k != "type"})


APP = {
    "en": {
        "days_left": "{n} days to Durga visarjan (20 Oct 2026)",
        "days_today": "Durga visarjan is today (20 Oct 2026)",
        "tagline": "Which ghats need cleaning, aeration or a fresh water test before visarjan - from 3 years of MPPCB test reports.",
        "dispatch_title": "Work list",
        "list": {"clean": "Send cleaning crew", "aerate": "Arrange aeration", "retest": "Take fresh water sample"},
        "none": "None",
        "gap_mark": "data gap",
        "incl_ganesh": "Also use Ganesh visarjan tests (same lakes, more evidence)",
        "ranking_title": "Ghats, highest risk first",
        "latest_title": "Latest {festival} test ({year}) against the limit",
        "latest_none": "No {festival} test table for this ghat.",
        "limit_row": "Limit",
        "ok": "within limit", "bad": "beyond limit",
        "all_readings": "All readings with report page",
        "download": "Download brief (Hindi + English, print to PDF)",
        "col_param": "Parameter", "col_festival": "Festival", "col_year": "Year", "col_phase": "Phase", "col_value": "Printed value",
        "col_page": "Report page", "col_state": "Status",
        "state": {"value": "measured", "very_low": "below detection", "missing": "MISSING - not counted as clean"},
        "footer": "Ranking aid only, not a health or safety certificate. Missing readings are never counted as clean. "
                  "Units assumed (reports print none). No coliform data.",
    },
    "hi": {
        "days_left": "दुर्गा विसर्जन (20 अक्टूबर 2026) में {n} दिन शेष",
        "days_today": "दुर्गा विसर्जन आज है (20 अक्टूबर 2026)",
        "tagline": "विसर्जन से पहले किन घाटों पर सफ़ाई, वायुकरण या नए पानी की जाँच चाहिए - MPPCB की 3 वर्षों की जाँच रिपोर्टों से।",
        "dispatch_title": "कार्य-सूची",
        "list": {"clean": "सफ़ाई दल भेजें", "aerate": "वायुकरण कराएँ", "retest": "पानी का नया नमूना लें"},
        "none": "कोई नहीं",
        "gap_mark": "डेटा अधूरा",
        "incl_ganesh": "गणेश विसर्जन की जाँचें भी लें (वही झीलें, अधिक प्रमाण)",
        "ranking_title": "घाट - सबसे अधिक जोखिम पहले",
        "latest_title": "नवीनतम {festival} जाँच ({year}) - मानक के विरुद्ध",
        "latest_none": "इस घाट की {festival} जाँच तालिका नहीं है।",
        "limit_row": "मानक",
        "ok": "मानक के भीतर", "bad": "मानक से बाहर",
        "all_readings": "रिपोर्ट पृष्ठ सहित सभी रीडिंग",
        "download": "संक्षिप्त रिपोर्ट डाउनलोड करें (हिन्दी + English, PDF के लिए प्रिंट करें)",
        "col_param": "पैरामीटर", "col_festival": "त्योहार", "col_year": "वर्ष", "col_phase": "चरण", "col_value": "छपा मान",
        "col_page": "रिपोर्ट पृष्ठ", "col_state": "स्थिति",
        "state": {"value": "मापा गया", "very_low": "पहचान सीमा से कम", "missing": "उपलब्ध नहीं - साफ़ नहीं माना गया"},
        "footer": "यह केवल प्राथमिकता तय करने का साधन है, स्वास्थ्य या सुरक्षा प्रमाणपत्र नहीं। अनुपलब्ध रीडिंग को कभी साफ़ नहीं माना गया। "
                  "इकाइयाँ मानी गई हैं (रिपोर्ट में नहीं छपीं)। कोलीफ़ॉर्म डेटा नहीं है।",
    },
}
