"""Kundli Milan: Ashtakoota marriage matching (Streamlit app).

Run locally:   streamlit run app.py
"""
from __future__ import annotations

import os
from datetime import date, time, timedelta

import streamlit as st

from kundli.engine import ACCURACY_WINDOWS, NAK_SPAN, Chart, calculate_chart, sweep
from kundli.i18n import LANGUAGES, M, Name, tr
from kundli.manual import nakshatras_in_rashi, padas_in
from kundli.matching import (ABSENT, CANCELLED, MITIGATED, NOT_CHECKED, Person,
                             match)
from kundli.places import (Place, all_timezones, local_day_bounds_utc,
                           resolve_local_time, search_places)
from kundli.report import build_facts, koota_quality, moon_text, to_markdown

st.set_page_config(page_title="Kundli Milan", page_icon="🪔", layout="wide")


def secret(name: str, default: str | None = None) -> str | None:
    try:
        value = st.secrets.get(name)
    except Exception:          # no secrets file configured
        value = None
    return value or os.environ.get(name) or default


# ------------------------------------------------------------- language
_, lang_col = st.columns([3, 1])
LANG = lang_col.radio(tr(M("language"), "en"), list(LANGUAGES),
                      format_func=LANGUAGES.get, horizontal=True, key="lang")


def t(key: str, **params) -> str:
    return tr(M(key, **params), LANG)


def T(x) -> str:
    return tr(x, LANG)


# ------------------------------------------------------------ password gate
APP_PASSWORD = secret("APP_PASSWORD")
if APP_PASSWORD and not st.session_state.get("authed"):
    st.title("🪔 " + t("title"))
    pw = st.text_input(t("password"), type="password")
    if pw:
        if pw == APP_PASSWORD:
            st.session_state.authed = True
            st.rerun()
        st.error(t("wrong_password"))
    st.stop()


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def cached_search(query: str) -> list[Place]:
    return search_places(query)


ACCURACY_KEYS = ["exact", "approx_15m", "approx_1h", "unknown"]


def month_name(m: int) -> str:
    return T(Name("month", m - 1))


def translated_select(label: str, options: list, fmt, key: str,
                      default=None, placeholder: str | None = None):
    """Selectbox whose option labels change with the language. Streamlit
    keeps showing the old label of an already-selected option, so the widget
    gets a per-language key while the chosen value is carried over."""
    store = f"{key}__value"
    current = st.session_state.get(store, default)
    index = options.index(current) if current in options else None
    value = st.selectbox(label, options, index=index, format_func=fmt,
                         placeholder=placeholder or "", key=f"{key}__{LANG}")
    st.session_state[store] = value
    return value


# ------------------------------------------------------------------ inputs
def star_form(name: str, key: str) -> dict:
    """Rashi + nakshatra (+ optional pada) entry."""
    rashi = translated_select(t("rashi_q"), list(range(12)),
                              lambda r: T(Name("rashi", r)), f"{key}_rashi")
    nak = pada = None
    if rashi is not None:
        naks = nakshatras_in_rashi(rashi)
        nak = translated_select(t("nak_q"), naks,
                                lambda n: T(Name("nakshatra", n)),
                                f"{key}_nak_{rashi}")
        if nak is not None:
            pada = translated_select(t("pada_q"), [0] + padas_in(rashi, nak),
                                     lambda p: t("pada_value", p=p) if p else t("pada_unknown"),
                                     f"{key}_pada_{rashi}_{nak}", default=0)
    manglik = translated_select(t("manglik_q"), ["unknown", "yes", "no"],
                                lambda m: t(f"manglik_{m}"), f"{key}_manglik",
                                default="unknown")
    st.caption(t("star_info"))
    return {"mode": "star", "name": name.strip(), "rashi": rashi, "nak": nak,
            "pada": pada or None,
            "manglik": {"yes": True, "no": False}.get(manglik)}


def person_form(role: str, key: str) -> dict:
    st.subheader(t(role))
    name = st.text_input(t("full_name"), key=f"{key}_name")
    mode = translated_select(t("mode_label"), ["birth", "star"],
                             lambda m: t(f"mode_{m}"), f"{key}_mode",
                             default="birth")
    if mode == "star":
        return star_form(name, key)
    st.markdown(t("dob"))
    c1, c2, c3 = st.columns(3)
    day = c1.selectbox(t("day"), list(range(1, 32)), index=None,
                       placeholder="DD", key=f"{key}_dd")
    with c2:
        month = translated_select(t("month"), list(range(1, 13)), month_name,
                                  f"{key}_mon", placeholder=t("month"))
    year = c3.selectbox(t("year"), list(range(date.today().year, 1899, -1)),
                        index=None, placeholder="YYYY", key=f"{key}_yyyy")
    dob = None
    if day and month and year:
        try:
            dob = date(year, month, day)
        except ValueError:
            st.error(t("invalid_date", month=month_name(month), year=year, day=day))

    accuracy = translated_select(t("accuracy_q"), ACCURACY_KEYS,
                                 lambda k: t(f"acc_{k}"), f"{key}_acc",
                                 default="exact")
    tm = None
    if accuracy != "unknown":
        c1, c2, c3 = st.columns(3)
        hour = c1.selectbox(t("hour"), list(range(1, 13)), index=None,
                            placeholder="HH", key=f"{key}_h")
        minute = c2.selectbox(t("minute"), list(range(60)), index=None,
                              placeholder="MM", format_func=lambda m: f"{m:02d}",
                              key=f"{key}_m")
        with c3:
            ampm = translated_select("AM / PM", ["AM", "PM"], t, f"{key}_ampm",
                                     placeholder="AM/PM")
        if hour is not None and minute is not None and ampm:
            tm = time(hour % 12 + (12 if ampm == "PM" else 0), minute)
            hint = ""
            if hour == 12:
                hint = t("hint_midnight") if ampm == "AM" else t("hint_noon")
            st.caption(t("time24", t=f"{tm:%H:%M}", hint=hint))

    manual = st.checkbox(t("manual_coords"), key=f"{key}_manual")
    place = None
    if manual:
        c1, c2 = st.columns(2)
        lat = c1.number_input(t("lat"), -90.0, 90.0, value=None,
                              format="%.4f", key=f"{key}_lat")
        lon = c2.number_input(t("lon"), -180.0, 180.0, value=None,
                              format="%.4f", key=f"{key}_lon")
        tzs = all_timezones()
        tz = st.selectbox(t("timezone"), tzs, index=tzs.index("Asia/Kolkata"),
                          key=f"{key}_tz")
        if lat is not None and lon is not None:
            place = Place("Manual location", "", "", lat, lon, tz)
    else:
        query = st.text_input(t("place_q"), placeholder=t("place_ph"),
                              key=f"{key}_q").strip()
        if len(query) >= 2:
            try:
                results = cached_search(query)
            except Exception:
                results = None
                st.warning(t("place_fail"))
            if results:
                place = st.selectbox(t("choose_place"), results,
                                     format_func=lambda p: p.label,
                                     key=f"{key}_place")
            elif results == []:
                st.info(t("no_match"))

    override = None
    if st.checkbox(t("override"), key=f"{key}_ovr"):
        c1, c2, c3 = st.columns(3)
        sign = c1.selectbox(t("sign"), ["+", "-"], key=f"{key}_osign")
        oh = c2.number_input(t("hours"), 0, 14, 5, key=f"{key}_oh")
        om = c3.number_input(t("minutes"), 0, 59, 30, key=f"{key}_om")
        override = (1 if sign == "+" else -1) * timedelta(hours=oh, minutes=om)

    return {"mode": "birth", "name": name.strip(), "dob": dob,
            "accuracy": accuracy, "time": tm, "place": place, "override": override}


def resolve(form: dict):
    missing = []
    if not form["name"]:
        missing.append("need_name")
    if form["mode"] == "star":
        if form["rashi"] is None:
            missing.append("need_rashi")
        elif form["nak"] is None:
            missing.append("need_nak")
        return None, missing
    if form["dob"] is None:
        missing.append("need_dob")
    if form["accuracy"] != "unknown" and form["time"] is None:
        missing.append("need_time")
    if form["place"] is None:
        missing.append("need_place")
    if missing:
        return None, missing
    tm = form["time"] if form["accuracy"] != "unknown" else time(12, 0)
    rt = resolve_local_time(form["dob"], tm, form["place"].timezone, form["override"])
    return rt, []


def resolved_text(form: dict, rt, lang: str) -> str:
    if form["mode"] == "star":
        pada = (tr(M("pada_value", p=form["pada"]), lang) if form["pada"]
                else tr(M("pada_not_given"), lang))
        return tr(M("entered_text", rashi=Name("rashi", form["rashi"]),
                    nak=Name("nakshatra", form["nak"]), pada=pada), lang)
    p = form["place"]
    d = f"{form['dob']:%d}-{tr(Name('month', form['dob'].month - 1), lang)}-{form['dob']:%Y}"
    when = (tr(M("when_unknown", date=d), lang) if form["accuracy"] == "unknown"
            else tr(M("when_known", date=d, time=f"{rt.local:%H:%M}"), lang))
    source = tr(Name("offset_source", rt.offset_source), lang)
    return (f"{when}; {rt.tz_name}, {rt.offset_label} ({source}); "
            f"= {rt.utc:%Y-%m-%d %H:%M} UTC; {p.latitude:.4f}, {p.longitude:.4f}")


def show_resolved(form: dict, rt, missing: list[str]) -> None:
    if missing:
        st.caption(t("still_needed", items=", ".join(t(m) for m in missing)))
        return
    st.markdown(t("please_check", text=resolved_text(form, rt, LANG)))
    if form["mode"] == "star":
        return
    if form["accuracy"] == "unknown":
        st.info(t("unknown_info"))
    for n in rt.notes:
        st.warning(T(n))


def build_person(form: dict, rt) -> Person:
    if form["mode"] == "star":
        return Person.from_rashi_nakshatra(form["name"], form["rashi"], form["nak"],
                                           form["pada"], form["manglik"])
    p = form["place"]
    lagna_known = form["accuracy"] != "unknown"
    chart = calculate_chart(rt.utc, p.latitude, p.longitude, with_lagna=lagna_known)
    if lagna_known:
        w = timedelta(minutes=ACCURACY_WINDOWS[form["accuracy"]])
        sw = sweep(chart, rt.utc - w, rt.utc + w, p.latitude, p.longitude,
                   True, step_minutes=1 if w <= timedelta(minutes=15) else 2)
    else:
        start, end = local_day_bounds_utc(form["dob"], rt.utc_offset)
        sw = sweep(chart, start, end, p.latitude, p.longitude, False, step_minutes=5)
    return Person.from_chart(form["name"], chart, sw, lagna_known)


def signature(form: dict) -> tuple:
    return tuple(sorted(form.items()))


# ----------------------------------------------------------------- display
def dms(x: float) -> str:
    d = int(x)
    m_float = (x - d) * 60
    m = int(m_float)
    s = int(round((m_float - m) * 60))
    if s == 60:
        m, s = m + 1, 0
    if m == 60:
        d, m = d + 1, 0
    return f"{d}°{m:02d}'{s:02d}\""


def chart_table(person: Person) -> str:
    ch: Chart = person.chart
    rows = [f"| {t('col_body')} | {t('col_sign')} | {t('col_degree')} | {t('col_nak')} |",
            "|---|---|---|---|"]
    bodies = []
    if person.lagna_known and ch.lagna_lon is not None:
        bodies.append(("Lagna", ch.lagna_lon))
    bodies += [(n, ch.longitudes[n]) for n in ("Sun", "Moon", "Mars", "Mercury",
                                               "Jupiter", "Venus", "Saturn",
                                               "Rahu", "Ketu")]
    for name, lon in bodies:
        nak = int(lon // NAK_SPAN)
        pada = int((lon % NAK_SPAN) // (NAK_SPAN / 4)) + 1
        label = T(Name("planet", name))
        if name == "Lagna":
            label = f"**{label}**"
        rows.append(f"| {label} | {T(Name('rashi', int(lon // 30)))} | {dms(lon % 30)} | "
                    f"{T(Name('nakshatra', nak))} ({pada}) |")
    return "\n".join(rows)


def show_results(res: dict) -> None:
    bride, groom, r = res["bride"], res["groom"], res["result"]
    resolved = {role: resolved_text(f, rt, LANG) for role, (f, rt) in res["inputs"].items()}
    st.divider()
    st.header(f"{bride.name} & {groom.name}")

    c1, c2, c3 = st.columns(3)
    c1.metric(t("score_metric"), f"{r.total:g} / 36")
    c2.markdown(f"**{t('band_label')}**  \n{T(Name('band', r.band))}")
    if r.score_min != r.score_max:
        c3.metric(t("range_label"), t("range_value", a=r.score_min, b=r.score_max))
    st.progress(min(r.total / 36, 1.0))

    st.subheader(t("ashtakoota"))
    rows = [f"| {t('col_koota')} | {t('bride')} | {t('groom')} | {t('col_score')} |",
            "|---|---|---|---|"]
    for k in r.kootas:
        rows.append(f"| **{T(k.name)}** ({k.max:g}) | {T(k.bride)} | {T(k.groom)} | "
                    f"**{k.score:g}** / {k.max:g} |")
    st.markdown("\n".join(rows))

    with st.expander(t("what_means")):
        for k in r.kootas:
            line = (f"**{T(k.name)} ({k.score:g}/{k.max:g}, "
                    f"{T(koota_quality(k.score, k.max))}):** {t('meaning_' + k.key)}")
            if k.note:
                line += f" *{T(k.note)}*"
            st.markdown(line)

    st.subheader(t("doshas_header"))
    st.caption(t("doshas_caption"))
    for f in r.doshas:
        body = f"**{T(f.title)}: {T(Name('status', f.status))}**"
        if f.time_sensitive:
            body += "  " + t("depends_time")
        body += "\n" + "\n".join(f"- {T(d)}" for d in f.details)
        if f.parihara:
            body += "\n\n" + t("parihara_applied") + "\n" + "\n".join(
                f"- {T(p)}" for p in f.parihara)
        {ABSENT: st.success, CANCELLED: st.info, MITIGATED: st.warning,
         NOT_CHECKED: st.info}.get(f.status, st.error)(body)

    if r.sensitivity_notes:
        st.subheader(t("sensitivity_header"))
        for n in r.sensitivity_notes:
            st.warning(T(n))

    st.subheader(t("chart_details"))
    c1, c2 = st.columns(2)
    for col, role, p in ((c1, "bride", bride), (c2, "groom", groom)):
        with col, st.expander(t("chart_of", name=p.name), expanded=False):
            st.caption(resolved[role])
            st.markdown(t("moon_label", state=moon_text(p, LANG)))
            if p.chart is None:
                st.caption(t("chart_entered"))
                continue
            st.markdown(chart_table(p))
            st.caption(t("chart_caption", aya=dms(p.chart.ayanamsa),
                         eph=p.chart.ephemeris))

    # ---------------------------------------------------- optional AI
    api_key = secret("ANTHROPIC_API_KEY")
    ai = st.session_state.get("ai")
    if api_key:
        st.subheader(t("ai_header"))
        ai_langs = ["English", "Kannada", "Hindi", "Tamil", "Telugu", "Marathi",
                    "Bengali", "Gujarati", "Malayalam"]
        c1, c2 = st.columns([1, 2])
        ai_lang = c1.selectbox(t("ai_language"), ai_langs,
                               index=1 if LANG == "kn" else 0)
        c2.write("")
        if c2.button(t("ai_button")):
            from kundli.ai import DEFAULT_MODEL, AIError, generate_interpretation
            with st.spinner(t("ai_spinner")):
                try:
                    ai = generate_interpretation(
                        build_facts(bride, groom, r), api_key,
                        secret("ANTHROPIC_MODEL", DEFAULT_MODEL), ai_lang)
                    st.session_state.ai = ai
                except AIError as e:
                    st.error(str(e))
        if ai:
            text, warns = ai
            for w in warns:
                st.warning(w)
            st.markdown(text)
            st.caption(t("ai_caption"))

    st.download_button(
        t("download"),
        data=to_markdown(bride, groom, r, resolved, LANG, ai[0] if ai else None),
        file_name=f"kundli-milan-{bride.name}-{groom.name}.md".replace(" ", "_"),
        mime="text/markdown",
    )


# --------------------------------------------------------------------- page
st.title("🪔 " + t("title"))
st.caption(t("caption"))

col_b, col_g = st.columns(2, gap="large")
with col_b:
    bride_form = person_form("bride", "b")
    bride_rt, b_missing = resolve(bride_form)
    show_resolved(bride_form, bride_rt, b_missing)
with col_g:
    groom_form = person_form("groom", "g")
    groom_rt, g_missing = resolve(groom_form)
    show_resolved(groom_form, groom_rt, g_missing)

st.write("")
current_sig = (signature(bride_form), signature(groom_form))
if st.button(t("calc_button"), type="primary", disabled=bool(b_missing or g_missing)):
    with st.spinner(t("calculating")):
        bride = build_person(bride_form, bride_rt)
        groom = build_person(groom_form, groom_rt)
        st.session_state.match = {
            "sig": current_sig,
            "bride": bride,
            "groom": groom,
            "result": match(bride, groom),
            "inputs": {"bride": (bride_form, bride_rt), "groom": (groom_form, groom_rt)},
        }
        st.session_state.ai = None

res = st.session_state.get("match")
if res:
    if res["sig"] != current_sig:
        st.info(t("details_changed"))
    else:
        show_results(res)

st.divider()
st.caption(t("footer"))
