"""Kundli Milan: Ashtakoota marriage matching (Streamlit app).

Run locally:   streamlit run app.py
"""
from __future__ import annotations

import os
from datetime import date, time, timedelta

import streamlit as st

from kundli import data as D
from kundli.engine import ACCURACY_WINDOWS, NAK_SPAN, Chart, calculate_chart, sweep
from kundli.matching import ABSENT, CANCELLED, MITIGATED, Person, match
from kundli.places import (Place, all_timezones, local_day_bounds_utc,
                           resolve_local_time, search_places)
from kundli.report import KOOTA_MEANING, build_facts, koota_quality, to_markdown

st.set_page_config(page_title="Kundli Milan", page_icon="🪔", layout="wide")


def secret(name: str, default: str | None = None) -> str | None:
    try:
        value = st.secrets.get(name)
    except Exception:          # no secrets file configured
        value = None
    return value or os.environ.get(name) or default


# ------------------------------------------------------------ password gate
APP_PASSWORD = secret("APP_PASSWORD")
if APP_PASSWORD and not st.session_state.get("authed"):
    st.title("🪔 Kundli Milan")
    pw = st.text_input("Password", type="password")
    if pw:
        if pw == APP_PASSWORD:
            st.session_state.authed = True
            st.rerun()
        st.error("Wrong password.")
    st.stop()


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def cached_search(query: str) -> list[Place]:
    return search_places(query)


MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

ACCURACY_OPTIONS = {
    "exact": "Exact (birth certificate / hospital record)",
    "approx_15m": "Approximate (within about 15 minutes)",
    "approx_1h": "Rough (within about an hour)",
    "unknown": "Unknown",
}


# ------------------------------------------------------------------ inputs
def person_form(title: str, key: str) -> dict:
    st.subheader(title)
    name = st.text_input("Full name", key=f"{key}_name")
    st.markdown("Date of birth")
    c1, c2, c3 = st.columns(3)
    day = c1.selectbox("Day", list(range(1, 32)), index=None, placeholder="DD",
                       key=f"{key}_dd")
    month = c2.selectbox("Month", list(range(1, 13)), index=None,
                         placeholder="Month", format_func=lambda m: MONTHS[m - 1],
                         key=f"{key}_mon")
    year = c3.selectbox("Year", list(range(date.today().year, 1899, -1)),
                        index=None, placeholder="YYYY", key=f"{key}_yyyy")
    dob = None
    if day and month and year:
        try:
            dob = date(year, month, day)
        except ValueError:
            st.error(f"{MONTHS[month - 1]} {year} has no day {day}.")
    accuracy = st.selectbox("How accurate is the birth time?",
                            list(ACCURACY_OPTIONS),
                            format_func=ACCURACY_OPTIONS.get, key=f"{key}_acc")
    t = None
    if accuracy != "unknown":
        c1, c2, c3 = st.columns(3)
        hour = c1.selectbox("Hour", list(range(1, 13)), index=None,
                            placeholder="HH", key=f"{key}_h")
        minute = c2.selectbox("Minute", list(range(60)), index=None,
                              placeholder="MM", format_func=lambda m: f"{m:02d}",
                              key=f"{key}_m")
        ampm = c3.selectbox("AM / PM", ["AM", "PM"], index=None,
                            placeholder="AM/PM", key=f"{key}_ampm")
        if hour is not None and minute is not None and ampm:
            t = time(hour % 12 + (12 if ampm == "PM" else 0), minute)
            hint = ""
            if hour == 12:
                hint = " (just after midnight)" if ampm == "AM" else " (noon)"
            st.caption(f"24-hour time: **{t:%H:%M}**{hint}")

    manual = st.checkbox("Enter coordinates manually instead of searching",
                         key=f"{key}_manual")
    place = None
    if manual:
        c1, c2 = st.columns(2)
        lat = c1.number_input("Latitude (north +)", -90.0, 90.0, value=None,
                              format="%.4f", key=f"{key}_lat")
        lon = c2.number_input("Longitude (east +)", -180.0, 180.0, value=None,
                              format="%.4f", key=f"{key}_lon")
        tzs = all_timezones()
        tz = st.selectbox("Timezone", tzs, index=tzs.index("Asia/Kolkata"),
                          key=f"{key}_tz")
        if lat is not None and lon is not None:
            place = Place("Manual location", "", "", lat, lon, tz)
    else:
        query = st.text_input("Place of birth (city or town name only)",
                              placeholder="e.g. Mysuru", key=f"{key}_q").strip()
        if len(query) >= 2:
            try:
                results = cached_search(query)
            except Exception:
                results = None
                st.warning("Place lookup failed. Check the internet connection, "
                           "or tick 'Enter coordinates manually'.")
            if results:
                place = st.selectbox("Choose the exact place", results,
                                     format_func=lambda p: p.label,
                                     key=f"{key}_place")
            elif results == []:
                st.info("No match. Try another spelling (e.g. Bengaluru / "
                        "Bangalore) or enter coordinates manually.")

    override = None
    if st.checkbox("Override UTC offset (only if the timezone shown below is wrong)",
                   key=f"{key}_ovr"):
        c1, c2, c3 = st.columns(3)
        sign = c1.selectbox("Sign", ["+", "-"], key=f"{key}_osign")
        oh = c2.number_input("Hours", 0, 14, 5, key=f"{key}_oh")
        om = c3.number_input("Minutes", 0, 59, 30, key=f"{key}_om")
        override = (1 if sign == "+" else -1) * timedelta(hours=oh, minutes=om)

    return {"name": name.strip(), "dob": dob, "accuracy": accuracy, "time": t,
            "place": place, "override": override}


def resolve(form: dict):
    missing = []
    if not form["name"]:
        missing.append("name")
    if form["dob"] is None:
        missing.append("date of birth")
    if form["accuracy"] != "unknown" and form["time"] is None:
        missing.append("time of birth (hour, minute and AM/PM)")
    if form["place"] is None:
        missing.append("place of birth")
    if missing:
        return None, missing
    t = form["time"] if form["accuracy"] != "unknown" else time(12, 0)
    rt = resolve_local_time(form["dob"], t, form["place"].timezone, form["override"])
    return rt, []


def resolved_text(form: dict, rt) -> str:
    p = form["place"]
    when = (f"{form['dob']:%d %b %Y}, time unknown (noon used for the Moon)"
            if form["accuracy"] == "unknown"
            else f"{rt.local:%d %b %Y, %H:%M} local")
    return (f"{when}; {rt.tz_name}, {rt.offset_label} ({rt.offset_source}); "
            f"= {rt.utc:%d %b %Y %H:%M} UTC; "
            f"{p.latitude:.4f}, {p.longitude:.4f}")


def show_resolved(form: dict, rt, missing: list[str]) -> None:
    if missing:
        st.caption("Still needed: " + ", ".join(missing))
        return
    st.markdown("**Please check:** " + resolved_text(form, rt))
    if form["accuracy"] == "unknown":
        st.info("Birth time unknown: the Lagna can't be used, and the Moon is "
                "checked across the whole day.")
    for n in rt.notes:
        st.warning(n)


def build_person(form: dict, rt) -> Person:
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
    return Person(form["name"], chart, sw, lagna_known)


def signature(form: dict) -> tuple:
    return tuple(form[k] for k in ("name", "dob", "accuracy", "time", "place", "override"))


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
    rows = ["| Body | Sign | Degree | Nakshatra (pada) |", "|---|---|---|---|"]
    if person.lagna_known and ch.lagna_lon is not None:
        L = ch.lagna_lon
        rows.append(f"| **Lagna** | {D.RASHIS[int(L // 30)]} | {dms(L % 30)} | "
                    f"{D.NAKSHATRAS[int(L // NAK_SPAN)]} |")
    for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                 "Saturn", "Rahu", "Ketu"):
        lon = ch.longitudes[name]
        nak = int(lon // NAK_SPAN)
        pada = int((lon % NAK_SPAN) // (NAK_SPAN / 4)) + 1
        rows.append(f"| {name} | {D.RASHIS[int(lon // 30)]} | {dms(lon % 30)} | "
                    f"{D.NAKSHATRAS[nak]} ({pada}) |")
    return "\n".join(rows)


def show_results(res: dict) -> None:
    bride, groom, r = res["bride"], res["groom"], res["result"]
    st.divider()
    st.header(f"{bride.name} & {groom.name}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Guna Milan score", f"{r.total:g} / 36")
    c2.markdown(f"**Band**  \n{r.band}")
    if r.score_min != r.score_max:
        c3.metric("Range if the birth time is slightly off",
                  f"{r.score_min:g} to {r.score_max:g}")
    st.progress(min(r.total / 36, 1.0))

    st.subheader("Ashtakoota")
    rows = ["| Koota | Bride | Groom | Score |", "|---|---|---|---|"]
    for k in r.kootas:
        rows.append(f"| **{k.name}** ({k.max:g}) | {k.bride} | {k.groom} | "
                    f"**{k.score:g}** / {k.max:g} |")
    st.markdown("\n".join(rows))

    with st.expander("What each koota means"):
        for k in r.kootas:
            line = (f"**{k.name} ({k.score:g}/{k.max:g}, "
                    f"{koota_quality(k.score, k.max)}):** {KOOTA_MEANING[k.key]}")
            if k.note:
                line += f" *{k.note}*"
            st.markdown(line)

    st.subheader("Doshas and cancellations")
    st.caption("A cancellation (parihara) doesn't change the 36-point score; "
               "it changes whether the dosha is traditionally a concern.")
    for f in r.doshas:
        body = f"**{f.title}: {f.status}**"
        if f.time_sensitive:
            body += "  ⏱️ *depends on exact birth time*"
        body += "\n" + "\n".join(f"- {d}" for d in f.details)
        if f.parihara:
            body += "\n\n*Parihara (cancellation) applied:*\n" + "\n".join(
                f"- {p}" for p in f.parihara)
        {ABSENT: st.success, CANCELLED: st.info,
         MITIGATED: st.warning}.get(f.status, st.error)(body)

    if r.sensitivity_notes:
        st.subheader("Birth-time sensitivity")
        for n in r.sensitivity_notes:
            st.warning(n)

    st.subheader("Chart details")
    c1, c2 = st.columns(2)
    for col, role, p in ((c1, "bride", bride), (c2, "groom", groom)):
        with col, st.expander(f"{p.name}'s chart", expanded=False):
            st.caption(res["resolved"][role])
            st.markdown(f"**Moon:** {p.chart.moon.describe()}")
            st.markdown(chart_table(p))
            st.caption(f"Lahiri ayanamsa {dms(p.chart.ayanamsa)} · "
                       f"{p.chart.ephemeris} · whole-sign houses")

    # ---------------------------------------------------- optional AI
    facts = build_facts(bride, groom, r)
    api_key = secret("ANTHROPIC_API_KEY")
    ai = st.session_state.get("ai")
    if api_key:
        st.subheader("Interpretation (AI)")
        c1, c2 = st.columns([1, 2])
        lang = c1.selectbox("Language", ["English", "Hindi", "Kannada", "Tamil",
                                         "Telugu", "Marathi", "Bengali",
                                         "Gujarati", "Malayalam"])
        c2.write("")
        if c2.button("Write interpretation"):
            from kundli.ai import DEFAULT_MODEL, AIError, generate_interpretation
            with st.spinner("Writing the interpretation (about 30 seconds)..."):
                try:
                    ai = generate_interpretation(
                        facts, api_key, secret("ANTHROPIC_MODEL", DEFAULT_MODEL), lang)
                    st.session_state.ai = ai
                except AIError as e:
                    st.error(str(e))
        if ai:
            text, warns = ai
            for w in warns:
                st.warning(w)
            st.markdown(text)
            st.caption("Written by AI from the calculated values above. The "
                       "table and dosha results are the source of truth.")

    st.download_button(
        "Download report (Markdown)",
        data=to_markdown(bride, groom, r, res["resolved"], ai[0] if ai else None),
        file_name=f"kundli-milan-{bride.name}-{groom.name}.md".replace(" ", "_"),
        mime="text/markdown",
    )


# --------------------------------------------------------------------- page
st.title("🪔 Kundli Milan")
st.caption("Ashtakoota (36 Guna) matching · Swiss Ephemeris · Lahiri ayanamsa")

col_b, col_g = st.columns(2, gap="large")
with col_b:
    bride_form = person_form("Bride", "b")
    bride_rt, b_missing = resolve(bride_form)
    show_resolved(bride_form, bride_rt, b_missing)
with col_g:
    groom_form = person_form("Groom", "g")
    groom_rt, g_missing = resolve(groom_form)
    show_resolved(groom_form, groom_rt, g_missing)

st.write("")
current_sig = (signature(bride_form), signature(groom_form))
if st.button("Details are correct: calculate match", type="primary",
             disabled=bool(b_missing or g_missing)):
    with st.spinner("Calculating charts..."):
        bride = build_person(bride_form, bride_rt)
        groom = build_person(groom_form, groom_rt)
        st.session_state.match = {
            "sig": current_sig,
            "bride": bride,
            "groom": groom,
            "result": match(bride, groom),
            "resolved": {"bride": resolved_text(bride_form, bride_rt),
                         "groom": resolved_text(groom_form, groom_rt)},
        }
        st.session_state.ai = None

res = st.session_state.get("match")
if res:
    if res["sig"] != current_sig:
        st.info("The details have changed. Click **calculate match** again "
                "to update the results.")
    else:
        show_results(res)

st.divider()
st.caption("For personal use. Calculations follow common North Indian "
           "Ashtakoota conventions; regional traditions differ. Astrology is "
           "one input among many: values, respect and communication matter most.")
