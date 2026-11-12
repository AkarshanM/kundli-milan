"""Presentation helpers for an individual kundli: values shared by the page,
the Markdown download and the AI fact sheet."""
from __future__ import annotations

from . import data as D
from .horoscope import Horoscope, nakshatra_lord
from .i18n import M, Msg, Name, tr
from .matching import ABSENT, CANCELLED, PRESENT, DoshaFinding, severity_label
from .i18n import Join


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


def tithi_text(h: Horoscope, lang: str) -> str:
    p = h.panchanga
    i = p.tithi_in_paksha
    idx = i if i < 14 else (14 if p.paksha == "shukla" else 15)
    return tr(M("tithi_value", paksha=Name("paksha", p.paksha),
                tithi=Name("tithi", idx)), lang)


def masa_text(h: Horoscope, lang: str) -> str:
    c = h.chandramana
    name = Name("masa", c.masa)
    return tr(M("adhika", masa=name) if c.adhika else name, lang)


def cm_sentence(h: Horoscope, lang: str) -> str:
    """The traditional opening line of a Kannada jataka."""
    c, p = h.chandramana, h.panchanga
    i = p.tithi_in_paksha
    tithi = Name("tithi", i if i < 14 else (14 if p.paksha == "shukla" else 15))
    return tr(M("cm_sentence",
                samvatsara=Name("samvatsara", c.samvatsara),
                ayana=Name("ayana", "uttara" if c.uttarayana else "dakshina"),
                ritu=Name("ritu", c.ritu), masa=masa_text(h, lang),
                paksha=Name("paksha", p.paksha), tithi=tithi,
                vara=Name("vara", p.vara)), lang)


def chandramana_rows(h: Horoscope, lang: str) -> list[tuple[str, str]]:
    c = h.chandramana
    t = lambda k, **kw: tr(M(k, **kw), lang)  # noqa: E731
    rows = [
        (t("c_samvatsara"), tr(Name("samvatsara", c.samvatsara), lang)),
        (t("c_shaka"), str(c.shaka)),
        (t("c_ayana"), tr(Name("ayana", "uttara" if c.uttarayana else "dakshina"), lang)),
        (t("c_ritu"), tr(Name("ritu", c.ritu), lang)),
        (t("c_masa"), masa_text(h, lang)),
        (t("p_tithi"), tithi_text(h, lang)),
        (t("p_vara"), tr(Name("vara", h.panchanga.vara), lang)),
        (t("p_nakshatra"), tr(h.chart.moon.describe(), lang)),
        (t("p_yoga"), tr(Name("yoga", h.panchanga.yoga), lang)),
        (t("p_karana"), tr(Name("karana", h.panchanga.karana), lang)),
    ]
    if c.sunrise:
        rows.append((t("c_sunrise"), h.local_time(c.sunrise)))
    if c.sunset:
        rows.append((t("c_sunset"), h.local_time(c.sunset)))
    if c.ishtakala:
        rows.append((t("c_ishtakala"), t("ishta_value", g=c.ishtakala[0], v=c.ishtakala[1])))
    return rows


def chart_contents(h: Horoscope, lang: str, navamsa: bool = False) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    lagna = h.lagna_navamsa if navamsa else h.lagna_sign
    out.setdefault(lagna, []).append(tr(Name("planet_short", "Lagna"), lang))
    for p in h.planets:
        sign = p.navamsa if navamsa else p.sign
        label = tr(Name("planet_short", p.name), lang)
        if p.retro and p.name not in ("Rahu", "Ketu"):
            label += tr(M("retro_mark"), lang)
        out.setdefault(sign, []).append(label)
    return out


def planet_table_rows(h: Horoscope, lang: str) -> list[list[str]]:
    rows = []
    L = h.lagna_lon
    rows.append([f"**{tr(Name('planet', 'Lagna'), lang)}**",
                 tr(Name("rashi", h.lagna_sign), lang), dms(L % 30),
                 f"{tr(Name('nakshatra', int(L // (40 / 3))), lang)} "
                 f"({int((L % (40 / 3)) // (10 / 3)) + 1})",
                 tr(Name("planet", nakshatra_lord(int(L // (40 / 3)))), lang),
                 "1", tr(Name("rashi", h.lagna_navamsa), lang), ""])
    for p in h.planets:
        status = []
        if p.dignity:
            status.append(tr(Name("planet_status", p.dignity), lang))
        if p.retro and p.name not in ("Rahu", "Ketu"):
            status.append(tr(M("retro"), lang))
        rows.append([tr(Name("planet", p.name), lang),
                     tr(Name("rashi", p.sign), lang), dms(p.lon % 30),
                     f"{tr(Name('nakshatra', p.nakshatra), lang)} ({p.pada})",
                     tr(Name("planet", p.nak_lord), lang),
                     str(p.house), tr(Name("rashi", p.navamsa), lang),
                     ", ".join(status)])
    return rows


def avakahada(h: Horoscope) -> list[tuple[object, object]]:
    m = h.chart.moon
    return [
        (Name("koota", "varna"), Name("varna", D.RASHI_VARNA[m.rashi])),
        (Name("koota", "vashya"), Name("vashya", m.vashya)),
        (Name("koota", "yoni"), M("yoni_value",
                                  animal=Name("yoni", D.NAK_YONI[m.nakshatra]),
                                  sex=Name("sex", D.NAK_YONI_GENDER[m.nakshatra]))),
        (Name("koota", "gana"), Name("gana", D.NAK_GANA[m.nakshatra])),
        (Name("koota", "nadi"), Name("nadi", D.nadi_of(m.nakshatra))),
        (M("a_rashi_lord"), Name("planet", D.RASHI_LORD[m.rashi])),
        (M("a_nak_lord"), Name("planet", nakshatra_lord(m.nakshatra))),
    ]


def mangal_finding(h: Horoscope) -> DoshaFinding:
    m = h.mangal
    f = DoshaFinding("mangal", M("dosha_mangal", name=h.person.name), ABSENT)
    f.details.append(M("mangal_checked", refs=Join([Name("planet", r) for r in m.references])))
    f.details += m.house_exceptions
    if not m.raw:
        f.details.append(M("mangal_absent"))
        return f
    f.details.append(M("mangal_hits",
                       hits=Join([M("mangal_hit", house=hs, ref=Name("planet", n))
                                  for n, hs in m.hits]),
                       sev=Name("severity", severity_label(m.severity))))
    f.parihara = list(m.cancellations)
    f.status = CANCELLED if m.cancellations else PRESENT
    return f


def kaal_sarpa_finding(h: Horoscope) -> DoshaFinding:
    f = DoshaFinding("kaal_sarpa", M("kaal_sarpa_title"),
                     PRESENT if h.kaal_sarpa else ABSENT)
    f.details.append(M("kaal_sarpa_yes" if h.kaal_sarpa else "kaal_sarpa_no"))
    if h.kaal_sarpa:
        f.details.append(M("kaal_sarpa_note"))
    return f


def sade_sati_text(h: Horoscope) -> Msg:
    if h.sade_sati:
        return M("sade_sati_yes", phase=h.sade_sati,
                 desc=Name("sade_phase", h.sade_sati), sign=Name("rashi", h.saturn_now))
    return M("sade_sati_no", sign=Name("rashi", h.saturn_now))


def dasha_balance_msg(h: Horoscope) -> Msg:
    lord, y, m, d = h.balance
    return M("dasha_balance", lord=Name("planet", lord), y=y, m=m, d=d)


def current_dasha_msg(h: Horoscope) -> Msg | None:
    md, ad = h.current_dasha()
    if md is None or ad is None:
        return None
    return M("dasha_current", md=Name("planet", md.lord), ad=Name("planet", ad.lord),
             end=h.local_date(ad.end))


# ----------------------------------------------------------- AI fact sheet


def kundli_facts(h: Horoscope) -> dict:
    en = "en"
    m = h.chart.moon
    md, ad = h.current_dasha()
    return {
        "system": "Vedic (sidereal), Lahiri ayanamsa, whole-sign houses, Swiss Ephemeris",
        "name": h.person.name,
        "lagna": tr(Name("rashi", h.lagna_sign), en),
        "moon_sign": tr(Name("rashi", m.rashi), en),
        "nakshatra": f"{tr(Name('nakshatra', m.nakshatra), en)} pada {m.pada}",
        "planets": [
            {"planet": p.name, "sign": tr(Name("rashi", p.sign), en),
             "house": p.house, "nakshatra": tr(Name("nakshatra", p.nakshatra), en),
             "retrograde": p.retro and p.name not in ("Rahu", "Ketu"),
             "dignity": tr(Name("planet_status", p.dignity), en) if p.dignity else None,
             "navamsa": tr(Name("rashi", p.navamsa), en)}
            for p in h.planets
        ],
        "chandramana": None if not h.chandramana else dict(chandramana_rows(h, en)),
        "panchanga": {
            "vara": tr(Name("vara", h.panchanga.vara), en),
            "tithi": tithi_text(h, en),
            "yoga": tr(Name("yoga", h.panchanga.yoga), en),
            "karana": tr(Name("karana", h.panchanga.karana), en),
        },
        "avakahada": {tr(k, en): tr(v, en) for k, v in avakahada(h)},
        "doshas": [
            {"name": tr(f.title, en), "status": f.status,
             "details": [tr(x, en) for x in f.details],
             "cancellations": [tr(x, en) for x in f.parihara]}
            for f in (mangal_finding(h), kaal_sarpa_finding(h))
        ],
        "sade_sati_today": tr(sade_sati_text(h), en),
        "current_dasha": (None if md is None else
                          {"mahadasha": md.lord, "antardasha": ad.lord if ad else None,
                           "antardasha_ends": h.local_date(ad.end) if ad else None}),
        "birth_time_notes": [tr(n, en) for n in h.notes],
    }


# ---------------------------------------------------------------- Markdown


def kundli_markdown(h: Horoscope, lang: str, resolved: str,
                    ai_text: str | None = None, for_pdf: bool = False) -> str:
    """for_pdf=True emits [[CHART:D1]] / [[CHART:D9]] markers that the PDF
    builder replaces with drawn South Indian charts."""
    t = lambda key, **kw: tr(M(key, **kw), lang)  # noqa: E731
    T = lambda x: tr(x, lang)  # noqa: E731
    m = h.chart.moon
    lines = [f"# {t('kundli_title', name=h.person.name)}", ""]
    if h.chandramana:
        lines += [f"*{cm_sentence(h, lang)}*", ""]
    lines += [resolved, "",
             f"- **{t('k_lagna')}:** {T(Name('rashi', h.lagna_sign))}",
             f"- **{t('k_moon')}:** {T(m.describe())}",
             f"- **{t('k_sun')}:** {T(Name('rashi', h.chart.sign('Sun')))}",
             "", f"## {t('planets_header')}", "",
             f"| {t('col_body')} | {t('col_sign')} | {t('col_degree')} | {t('col_nak')} | "
             f"{t('col_nak_lord')} | {t('col_house')} | {t('col_navamsa')} | {t('col_status')} |",
             "|---|---|---|---|---|---|---|---|"]
    lines += ["| " + " | ".join(r) + " |" for r in planet_table_rows(h, lang)]

    if for_pdf:
        lines += ["", "[[CHARTS]]"]
    else:
        for title, nav in ((t("rashi_chart"), False), (t("navamsa_chart"), True)):
            lines += ["", f"### {title}", ""]
            contents = chart_contents(h, lang, nav)
            for s in range(12):
                if contents.get(s):
                    lines.append(f"- {T(Name('rashi', s))}: {', '.join(contents[s])}")

    if h.chandramana:
        lines += ["", f"## {t('cm_header')}", ""]
        lines += [f"- **{k}:** {v}" for k, v in chandramana_rows(h, lang)]
    else:
        p = h.panchanga
        lines += ["", f"## {t('panchanga_header')}", "",
                  f"- **{t('p_vara')}:** {T(Name('vara', p.vara))}",
                  f"- **{t('p_tithi')}:** {tithi_text(h, lang)}",
                  f"- **{t('p_nakshatra')}:** {T(Name('nakshatra', m.nakshatra))}",
                  f"- **{t('p_yoga')}:** {T(Name('yoga', p.yoga))}",
                  f"- **{t('p_karana')}:** {T(Name('karana', p.karana))}"]
    lines += ["", f"## {t('avakahada_header')}", ""]
    lines += [f"- **{T(k)}:** {T(v)}" for k, v in avakahada(h)]

    lines += ["", f"## {t('k_doshas_header')}", ""]
    for f in (mangal_finding(h), kaal_sarpa_finding(h)):
        lines.append(f"### {T(f.title)}: {T(Name('status', f.status))}")
        lines += [f"- {T(d)}" for d in f.details]
        lines += ["- " + t("md_parihara", p=x) for x in f.parihara]
        lines.append("")
    lines += [f"### {t('sade_sati_title')}", T(sade_sati_text(h)), ""]

    lines += [f"## {t('dasha_header')}", "", T(dasha_balance_msg(h))]
    cur = current_dasha_msg(h)
    if cur:
        lines.append(T(cur))
    lines += ["", f"| {t('col_mahadasha')} | {t('col_from')} | {t('col_to')} |", "|---|---|---|"]
    birth = h.chart.utc
    for md in h.dashas:
        start = h.local_date(max(md.start, birth))
        lines.append(f"| {T(Name('planet', md.lord))} | {start} | {h.local_date(md.end)} |")
    if h.notes:
        lines += ["", f"## {t('sensitivity_header')}", ""]
        lines += [f"- {T(n)}" for n in h.notes]
    if ai_text:
        lines += ["", f"## {t('md_interpretation')}", "", ai_text]
    lines += ["", "---", t("kundli_footer")]
    return "\n".join(lines)
