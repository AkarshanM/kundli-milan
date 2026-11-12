"""Fact sheet for the optional AI layer and the downloadable Markdown report."""
from __future__ import annotations

from .i18n import M, Name, tr
from .matching import MatchResult, Person
from . import data as D


def koota_quality(score: float, mx: float) -> Name:
    if score >= mx:
        return Name("quality", "full")
    if score <= 0:
        return Name("quality", "none")
    return Name("quality", "partial")


def lagna_text(p: Person, lang: str) -> str:
    if p.chart is not None and p.lagna_known and p.chart.lagna_rashi is not None:
        return tr(Name("rashi", p.chart.lagna_rashi), lang)
    return tr(M("lagna_unknown"), lang)


def moon_text(p: Person, lang: str) -> str:
    """Moon description; for directly entered data, don't invent a pada."""
    if p.entered and p.entered[2] is None:
        return tr(M("moon_state_no_pada", nak=Name("nakshatra", p.moon.nakshatra),
                    rashi=Name("rashi", p.moon.rashi)), lang)
    return tr(p.moon.describe(), lang)


def chart_summary(p: Person, lang: str = "en") -> dict:
    m = p.moon
    return {
        "name": p.name,
        "entered_as": "rashi and nakshatra" if p.chart is None else "birth details",
        "moon_nakshatra": tr(Name("nakshatra", m.nakshatra), lang),
        "moon_pada": None if (p.entered and p.entered[2] is None) else m.pada,
        "moon_sign": tr(Name("rashi", m.rashi), lang),
        "lagna": lagna_text(p, lang),
        "gana": tr(Name("gana", D.NAK_GANA[m.nakshatra]), lang),
        "nadi": tr(Name("nadi", D.nadi_of(m.nakshatra)), lang),
    }


def build_facts(bride: Person, groom: Person, r: MatchResult) -> dict:
    """Everything the AI layer may talk about, in English (the model writes
    in whichever language is requested). Contains no birth date, time or
    place."""
    en = "en"
    return {
        "system": "Karnataka Dashakoota (10 kootas, primary) and North Indian "
                  "Ashtakoota (36 gunas); Lahiri ayanamsa; Swiss Ephemeris",
        "bride": chart_summary(bride, en),
        "groom": chart_summary(groom, en),
        "total_score": r.total,
        "max_score": 36,
        "score_band": tr(Name("band", r.band), en),
        "score_range_within_birth_time_window": (
            None if r.score_min == r.score_max else [r.score_min, r.score_max]),
        "kootas": [
            {"name": tr(k.name, en), "score": k.score, "max": k.max,
             "bride": tr(k.bride, en), "groom": tr(k.groom, en),
             "note": tr(k.note, en) if k.note else "",
             "meaning": tr(M(f"meaning_{k.key}"), en)}
            for k in r.kootas
        ],
        "doshas": [
            {"name": tr(f.title, en), "status": f.status,
             "details": [tr(d, en) for d in f.details],
             "cancellation_rules_applied": [tr(p, en) for p in f.parihara],
             "depends_on_exact_birth_time": f.time_sensitive}
            for f in r.doshas
        ],
        "birth_time_sensitivity_notes": [tr(n, en) for n in r.sensitivity_notes],
        "dashakoota_karnataka": {
            "score": r.dk_total, "max": 10,
            "band": tr(Name("dk_band", r.dk_band), en),
            "kootas": [{"name": tr(k.name, en), "result": k.result,
                        "bride": tr(k.bride, en), "groom": tr(k.groom, en),
                        "meaning": tr(M(f"dk_meaning_{k.key}"), en)}
                       for k in r.dk],
        },
    }


KARNATAKA_DOSHAS = ("rajju", "vedha", "mangal_bride", "mangal_groom", "nadi")
NORTH_DOSHAS = ("nadi", "bhakoot", "gana", "mangal_bride", "mangal_groom")


def doshas_for(r: MatchResult, system: str):
    """The doshas each tradition puts first, in its usual order."""
    order = KARNATAKA_DOSHAS if system == "karnataka" else NORTH_DOSHAS
    by_key = {f.key: f for f in r.doshas}
    return [by_key[k] for k in order if k in by_key]


def dk_score_text(r: MatchResult) -> str:
    return f"{r.dk_total:g} / 10"


def _dk_table(r: MatchResult, lang: str, t) -> list[str]:
    lines = [f"| {t('col_koota')} | {t('bride')} | {t('groom')} | {t('col_result')} |",
             "|---|---|---|---|"]
    for k in r.dk:
        lines.append(f"| {tr(k.name, lang)} | {tr(k.bride, lang)} | {tr(k.groom, lang)} | "
                     f"{tr(Name('dk_result', k.result), lang)} |")
    return lines


def _ak_table(r: MatchResult, lang: str, t) -> list[str]:
    lines = [f"| {t('col_koota')} | {t('bride')} | {t('groom')} | {t('col_score')} |",
             "|---|---|---|---|"]
    for k in r.kootas:
        lines.append(f"| {tr(k.name, lang)} | {tr(k.bride, lang)} | "
                     f"{tr(k.groom, lang)} | {k.score:g} / {k.max:g} |")
    return lines


def to_markdown(bride: Person, groom: Person, r: MatchResult,
                resolved: dict[str, str], lang: str = "en",
                ai_text: str | None = None, system: str = "karnataka") -> str:
    t = lambda key, **kw: tr(M(key, **kw), lang)  # noqa: E731
    lines = ["# " + t("md_title", b=bride.name, g=groom.name), ""]
    if system == "karnataka":
        lines.append(f"**{t('dk_metric')}: {dk_score_text(r)}** "
                     f"({tr(Name('dk_band', r.dk_band), lang)})")
        if r.dk_min != r.dk_max:
            lines.append(t("md_range", a=r.dk_min, b=r.dk_max))
    else:
        lines.append(t("md_total", total=r.total, band=Name("band", r.band)))
        if r.score_min != r.score_max:
            lines.append(t("md_range", a=r.score_min, b=r.score_max))
    lines += ["", "## " + t("md_birth_data"), ""]
    for role, p in (("bride", bride), ("groom", groom)):
        lines.append(f"- **{t(role)}: {p.name}**: {resolved.get(role, '')}")
        lines.append("  - " + t("md_moon_line", moon=moon_text(p, lang),
                                lagna=lagna_text(p, lang)))
    if system == "karnataka":
        lines += ["", "## " + t("dk_header"), ""] + _dk_table(r, lang, t)
        lines += ["", "## " + t("ashtakoota_ref"),
                  "", t("md_total", total=r.total, band=Name("band", r.band)), ""]
        lines += _ak_table(r, lang, t)
    else:
        lines += ["", "## " + t("ashtakoota"), ""] + _ak_table(r, lang, t)
        lines += ["", "## " + t("dashakoota_ref"), "",
                  f"**{t('dk_metric')}: {dk_score_text(r)}**", ""] + _dk_table(r, lang, t)
    lines += ["", "## " + t("md_doshas"), ""]
    for f in doshas_for(r, system):
        lines.append(f"### {tr(f.title, lang)}: {tr(Name('status', f.status), lang)}")
        lines += [f"- {tr(d, lang)}" for d in f.details]
        lines += ["- " + t("md_parihara", p=p) for p in f.parihara]
        lines.append("")
    if r.sensitivity_notes:
        lines += ["## " + t("sensitivity_header"), ""]
        lines += [f"- {tr(n, lang)}" for n in r.sensitivity_notes]
        lines.append("")
    if ai_text:
        lines += ["## " + t("md_interpretation"), "", ai_text, ""]
    lines += ["---", t("md_footer")]
    return "\n".join(lines)
