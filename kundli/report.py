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
    if p.lagna_known and p.chart.lagna_rashi is not None:
        return tr(Name("rashi", p.chart.lagna_rashi), lang)
    return tr(M("lagna_unknown"), lang)


def chart_summary(p: Person, lang: str = "en") -> dict:
    m = p.chart.moon
    return {
        "name": p.name,
        "moon_nakshatra": tr(Name("nakshatra", m.nakshatra), lang),
        "moon_pada": m.pada,
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
        "system": "Ashtakoota (North Indian), Lahiri ayanamsa, Swiss Ephemeris",
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
    }


def to_markdown(bride: Person, groom: Person, r: MatchResult,
                resolved: dict[str, str], lang: str = "en",
                ai_text: str | None = None) -> str:
    t = lambda key, **kw: tr(M(key, **kw), lang)  # noqa: E731
    lines = [
        "# " + t("md_title", b=bride.name, g=groom.name),
        "",
        t("md_total", total=r.total, band=Name("band", r.band)),
    ]
    if r.score_min != r.score_max:
        lines.append(t("md_range", a=r.score_min, b=r.score_max))
    lines += ["", "## " + t("md_birth_data"), ""]
    for role, p in (("bride", bride), ("groom", groom)):
        lines.append(f"- **{t(role)}: {p.name}**: {resolved.get(role, '')}")
        lines.append("  - " + t("md_moon_line", moon=p.chart.moon.describe(),
                                lagna=lagna_text(p, lang)))
    lines += ["", "## " + t("ashtakoota"), "",
              f"| {t('col_koota')} | {t('bride')} | {t('groom')} | {t('col_score')} |",
              "|---|---|---|---|"]
    for k in r.kootas:
        lines.append(f"| {tr(k.name, lang)} | {tr(k.bride, lang)} | "
                     f"{tr(k.groom, lang)} | {k.score:g} / {k.max:g} |")
    lines += ["", "## " + t("md_doshas"), ""]
    for f in r.doshas:
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
