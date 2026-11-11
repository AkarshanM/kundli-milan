"""Plain-language explanations, the fact sheet sent to the optional AI layer,
and the downloadable Markdown report."""
from __future__ import annotations

from . import data as D
from .matching import MatchResult, Person

KOOTA_MEANING = {
    "varna": "Spiritual and work temperament (ego compatibility). Traditionally "
             "the groom's varna should be equal to or higher than the bride's. "
             "Here it describes temperament, not caste.",
    "vashya": "Mutual attraction and the balance of influence in the relationship.",
    "tara": "Birth-star (destiny) compatibility, counted from each partner's "
            "nakshatra to the other's.",
    "yoni": "Physical and instinctive compatibility, from the animal symbol of "
            "each nakshatra.",
    "maitri": "Mental wavelength and friendship, from the natural friendship "
              "between the two Moon-sign lords.",
    "gana": "Temperament: Deva (gentle), Manushya (balanced), Rakshasa (intense).",
    "bhakoot": "How the two Moon signs sit relative to each other. Traditionally "
               "linked with family welfare, finances and emotional harmony.",
    "nadi": "The most heavily weighted koota, traditionally linked with health "
            "and progeny. It is a traditional indicator, not a medical or "
            "genetic test.",
}


def koota_quality(score: float, mx: float) -> str:
    if score >= mx:
        return "full marks"
    if score <= 0:
        return "no marks"
    return "partial marks"


def chart_summary(p: Person) -> dict:
    ch = p.chart
    m = ch.moon
    return {
        "name": p.name,
        "moon_nakshatra": D.NAKSHATRAS[m.nakshatra],
        "moon_pada": m.pada,
        "moon_sign": D.RASHIS[m.rashi],
        "lagna": D.RASHIS[ch.lagna_rashi] if p.lagna_known and ch.lagna_rashi is not None else "unknown (birth time unknown)",
        "gana": D.GANA_NAMES[D.NAK_GANA[m.nakshatra]],
        "nadi": D.NADI_NAMES[D.nadi_of(m.nakshatra)],
    }


def build_facts(bride: Person, groom: Person, r: MatchResult) -> dict:
    """Everything the AI layer may talk about. Contains no birth date, time
    or place."""
    return {
        "system": "Ashtakoota (North Indian), Lahiri ayanamsa, Swiss Ephemeris",
        "bride": chart_summary(bride),
        "groom": chart_summary(groom),
        "total_score": r.total,
        "max_score": 36,
        "score_band": r.band,
        "score_range_within_birth_time_window": (
            None if r.score_min == r.score_max else [r.score_min, r.score_max]),
        "kootas": [
            {"name": k.name, "score": k.score, "max": k.max,
             "bride": k.bride, "groom": k.groom, "note": k.note,
             "meaning": KOOTA_MEANING[k.key]}
            for k in r.kootas
        ],
        "doshas": [
            {"name": f.title, "status": f.status, "details": f.details,
             "cancellation_rules_applied": f.parihara,
             "depends_on_exact_birth_time": f.time_sensitive}
            for f in r.doshas
        ],
        "birth_time_sensitivity_notes": r.sensitivity_notes,
    }


def to_markdown(bride: Person, groom: Person, r: MatchResult,
                resolved: dict[str, str], ai_text: str | None = None) -> str:
    lines = [
        f"# Kundli Milan: {bride.name} & {groom.name}",
        "",
        f"**Total: {r.total:g} / 36** ({r.band})",
    ]
    if r.score_min != r.score_max:
        lines.append(f"Score range within the birth-time window: "
                     f"{r.score_min:g}-{r.score_max:g}")
    lines += ["", "## Birth data used", ""]
    for role, p in (("Bride", bride), ("Groom", groom)):
        s = chart_summary(p)
        lines.append(f"- **{role}: {p.name}**: {resolved.get(role.lower(), '')}")
        lines.append(f"  - Moon: {s['moon_nakshatra']} pada {s['moon_pada']}, "
                     f"{s['moon_sign']}; Lagna: {s['lagna']}")
    lines += ["", "## Ashtakoota", "",
              "| Koota | Bride | Groom | Score |", "|---|---|---|---|"]
    for k in r.kootas:
        lines.append(f"| {k.name} | {k.bride} | {k.groom} | {k.score:g} / {k.max:g} |")
    lines += ["", "## Doshas", ""]
    for f in r.doshas:
        lines.append(f"### {f.title}: {f.status}")
        lines += [f"- {d}" for d in f.details]
        lines += [f"- Parihara: {p}" for p in f.parihara]
        lines.append("")
    if r.sensitivity_notes:
        lines += ["## Birth-time sensitivity", ""]
        lines += [f"- {n}" for n in r.sensitivity_notes]
        lines.append("")
    if ai_text:
        lines += ["## Interpretation", "", ai_text, ""]
    lines += ["---", "Calculated with Swiss Ephemeris (Lahiri ayanamsa). "
              "Astrology is one input among many: values, respect and "
              "communication matter most."]
    return "\n".join(lines)
