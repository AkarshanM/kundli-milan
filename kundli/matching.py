"""Ashtakoota scoring, dosha detection and cancellation (parihara) rules.

Everything here is deterministic. The AI layer only ever explains the output
of this module; it never computes anything.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

from . import data as D
from .engine import Chart, MoonPos, Sweep

# ---------------------------------------------------------------- kootas


@dataclass
class Koota:
    key: str
    name: str
    score: float
    max: float
    bride: str
    groom: str
    note: str = ""


def relation(a: str, b: str) -> str:
    """How planet a regards planet b."""
    if a == b:
        return "same"
    if b in D.FRIENDS[a]:
        return "friend"
    if b in D.ENEMIES[a]:
        return "enemy"
    return "neutral"


def maitri_points(lord_b: str, lord_g: str) -> float:
    if lord_b == lord_g:
        return 5.0
    pair = tuple(sorted([relation(lord_b, lord_g), relation(lord_g, lord_b)]))
    return D.MAITRI_POINTS[pair]


def tara_count(frm: int, to: int) -> int:
    return (to - frm) % 27 + 1


def tara_good(count: int) -> bool:
    return count % 9 not in D.BAD_TARA_REMAINDERS


def bhakoot_distance(bride_rashi: int, groom_rashi: int) -> int:
    return (groom_rashi - bride_rashi) % 12 + 1


def _yoni_label(nak: int) -> str:
    sex = "male" if D.NAK_YONI_GENDER[nak] == "M" else "female"
    return f"{D.YONI_ANIMALS[D.NAK_YONI[nak]]} ({sex})"


def score_kootas(b: MoonPos, g: MoonPos) -> list[Koota]:
    out: list[Koota] = []

    vb, vg = D.RASHI_VARNA[b.rashi], D.RASHI_VARNA[g.rashi]
    out.append(Koota("varna", "Varna", 1.0 if vg >= vb else 0.0, 1,
                     D.VARNA_NAMES[vb], D.VARNA_NAMES[vg]))

    cb, cg = b.vashya, g.vashya
    out.append(Koota("vashya", "Vashya", D.VASHYA_SCORE[cg][cb], 2,
                     D.VASHYA_CLASSES[cb], D.VASHYA_CLASSES[cg]))

    c_bg = tara_count(b.nakshatra, g.nakshatra)
    c_gb = tara_count(g.nakshatra, b.nakshatra)
    tara = 1.5 * tara_good(c_bg) + 1.5 * tara_good(c_gb)
    out.append(Koota(
        "tara", "Tara", tara, 3,
        f"{D.TARA_NAMES[c_bg % 9]} (groom's star is #{c_bg} from hers)",
        f"{D.TARA_NAMES[c_gb % 9]} (bride's star is #{c_gb} from his)",
        "Vipat, Pratyak and Naidhana are the unfavourable taras."))

    yb, yg = D.NAK_YONI[b.nakshatra], D.NAK_YONI[g.nakshatra]
    out.append(Koota("yoni", "Yoni", float(D.YONI_SCORE[yb][yg]), 4,
                     _yoni_label(b.nakshatra), _yoni_label(g.nakshatra)))

    lb, lg = D.RASHI_LORD[b.rashi], D.RASHI_LORD[g.rashi]
    out.append(Koota("maitri", "Graha Maitri", maitri_points(lb, lg), 5,
                     f"{lb} (lord of {D.RASHIS[b.rashi]})",
                     f"{lg} (lord of {D.RASHIS[g.rashi]})",
                     f"{lb} sees {lg} as {relation(lb, lg)}; "
                     f"{lg} sees {lb} as {relation(lg, lb)}."))

    gb, gg = D.NAK_GANA[b.nakshatra], D.NAK_GANA[g.nakshatra]
    out.append(Koota("gana", "Gana", D.GANA_SCORE[gg][gb], 6,
                     D.GANA_NAMES[gb], D.GANA_NAMES[gg]))

    d = bhakoot_distance(b.rashi, g.rashi)
    out.append(Koota("bhakoot", "Bhakoot",
                     0.0 if d in D.BAD_BHAKOOT else 7.0, 7,
                     D.RASHIS[b.rashi], D.RASHIS[g.rashi],
                     f"Moon signs are in a {D.BHAKOOT_LABEL[d]} relationship."))

    nb, ng = D.nadi_of(b.nakshatra), D.nadi_of(g.nakshatra)
    out.append(Koota("nadi", "Nadi", 0.0 if nb == ng else 8.0, 8,
                     D.NADI_NAMES[nb], D.NADI_NAMES[ng]))
    return out


def total_score(kootas: list[Koota]) -> float:
    return sum(k.score for k in kootas)


# ---------------------------------------------------------------- doshas

ABSENT, PRESENT, MITIGATED, CANCELLED = "Absent", "Present", "Mitigated", "Cancelled"


@dataclass
class DoshaFinding:
    key: str
    title: str
    status: str
    details: list[str] = field(default_factory=list)
    parihara: list[str] = field(default_factory=list)   # cancellation rules applied
    time_sensitive: bool = False


def _status(cancels: list[str], mitigations: list[str]) -> str:
    if cancels:
        return CANCELLED
    if mitigations:
        return MITIGATED
    return PRESENT


def nadi_dosha(b: MoonPos, g: MoonPos) -> DoshaFinding:
    nb, ng = D.nadi_of(b.nakshatra), D.nadi_of(g.nakshatra)
    f = DoshaFinding("nadi", "Nadi Dosha", ABSENT)
    if nb != ng:
        f.details.append(f"Different Nadis ({D.NADI_NAMES[nb]} / {D.NADI_NAMES[ng]}).")
        return f
    f.details.append(f"Both partners have {D.NADI_NAMES[nb]} Nadi (Nadi koota 0/8).")
    cancels, mitig = [], []
    lb, lg = D.RASHI_LORD[b.rashi], D.RASHI_LORD[g.rashi]
    if b.rashi == g.rashi and b.nakshatra != g.nakshatra:
        cancels.append("Same Moon sign but different nakshatras.")
    elif b.nakshatra == g.nakshatra and b.rashi != g.rashi:
        cancels.append("Same nakshatra but the Moons are in different signs.")
    elif b.nakshatra == g.nakshatra and b.pada != g.pada:
        mitig.append("Same nakshatra and sign but different padas "
                     "(accepted as a relief by some traditions).")
    if b.nakshatra == g.nakshatra and b.pada == g.pada:
        f.details.append("Same nakshatra and same pada: traditionally the "
                         "strongest form, with no standard cancellation.")
    if not cancels and lb != lg and relation(lb, lg) == "friend" and relation(lg, lb) == "friend":
        mitig.append(f"Moon-sign lords {lb} and {lg} are mutual friends "
                     "(accepted as a relief by some traditions).")
    f.status = _status(cancels, mitig)
    f.parihara = cancels + mitig
    return f


def bhakoot_dosha(b: MoonPos, g: MoonPos) -> DoshaFinding:
    d = bhakoot_distance(b.rashi, g.rashi)
    label = D.BHAKOOT_LABEL[d]
    f = DoshaFinding("bhakoot", "Bhakoot Dosha", ABSENT)
    if d not in D.BAD_BHAKOOT:
        f.details.append(f"Moon signs are {label} from each other, which is favourable.")
        return f
    f.details.append(f"Moon signs are {label} from each other (Bhakoot koota 0/7).")
    if label == "5/9":
        f.details.append("Some traditions treat 5/9 as milder than 6/8 or 2/12.")
    lb, lg = D.RASHI_LORD[b.rashi], D.RASHI_LORD[g.rashi]
    pts = maitri_points(lb, lg)
    cancels, mitig = [], []
    if lb == lg:
        cancels.append(f"Both Moon signs are ruled by {lb}.")
    elif pts == 5.0:
        cancels.append(f"Moon-sign lords {lb} and {lg} are mutual friends.")
    elif pts == 4.0:
        mitig.append(f"Moon-sign lords {lb} and {lg} are friendly on one side "
                     "and neutral on the other.")
    f.status = _status(cancels, mitig)
    f.parihara = cancels + mitig
    return f


def gana_dosha(b: MoonPos, g: MoonPos) -> DoshaFinding:
    gb, gg = D.NAK_GANA[b.nakshatra], D.NAK_GANA[g.nakshatra]
    pts = D.GANA_SCORE[gg][gb]
    f = DoshaFinding("gana", "Gana Dosha", ABSENT)
    if pts > 1:
        f.details.append(f"Ganas {D.GANA_NAMES[gb]} / {D.GANA_NAMES[gg]} are compatible.")
        return f
    f.details.append(f"Ganas {D.GANA_NAMES[gb]} (bride) and {D.GANA_NAMES[gg]} "
                     f"(groom) are a difficult pair (Gana koota {pts:g}/6).")
    lb, lg = D.RASHI_LORD[b.rashi], D.RASHI_LORD[g.rashi]
    maitri = maitri_points(lb, lg)
    cancels, mitig = [], []
    if maitri == 5.0:
        cancels.append("The Moon-sign lords are the same or mutual friends.")
    elif maitri == 4.0:
        mitig.append("The Moon-sign lords are friendly.")
    if bhakoot_distance(b.rashi, g.rashi) not in D.BAD_BHAKOOT:
        mitig.append("Bhakoot is favourable.")
    f.status = _status(cancels, mitig)
    f.parihara = cancels + mitig
    return f


# ------------------------------------------------------------ Mangal Dosha


@dataclass
class MangalPerson:
    references: list[str]
    hits: list[tuple[str, int]]
    house_exceptions: list[str]
    cancellations: list[str]
    severity: float

    @property
    def raw(self) -> bool:
        return bool(self.hits)

    @property
    def net(self) -> bool:
        return bool(self.hits) and not self.cancellations


def severity_label(sev: float) -> str:
    if sev <= 0:
        return "none"
    if sev <= 0.25:
        return "mild"
    if sev <= 0.5:
        return "moderate"
    return "strong"


def analyse_mangal(chart: Chart, lagna_known: bool) -> MangalPerson:
    mars = chart.sign("Mars")
    refs: list[tuple[str, int]] = []
    if lagna_known and chart.lagna_rashi is not None:
        refs.append(("Lagna", chart.lagna_rashi))
    refs += [("Moon", chart.moon.rashi), ("Venus", chart.sign("Venus"))]
    weights = ({"Lagna": 0.5, "Moon": 0.25, "Venus": 0.25}
               if refs[0][0] == "Lagna" else {"Moon": 0.5, "Venus": 0.5})

    hits, exceptions = [], []
    for name, ref in refs:
        house = (mars - ref) % 12 + 1
        if house not in D.MANGLIK_HOUSES:
            continue
        if mars in D.MANGLIK_HOUSE_SIGN_EXCEPTIONS.get(house, set()):
            exceptions.append(f"From {name}: Mars in house {house} in "
                              f"{D.RASHIS[mars]} is a traditional exception.")
        else:
            hits.append((name, house))

    cancellations: list[str] = []
    if hits:
        if mars in D.MARS_OWN_OR_EXALTED:
            cancellations.append(f"Mars is in {D.RASHIS[mars]}, its "
                                 f"{D.MARS_OWN_OR_EXALTED[mars]}.")
        rel = (mars - chart.sign("Jupiter")) % 12 + 1
        if rel == 1:
            cancellations.append("Mars is conjunct Jupiter.")
        elif rel in (5, 7, 9):
            cancellations.append(f"Mars receives Jupiter's aspect "
                                 f"(house {rel} from Jupiter).")
        if mars == chart.moon.rashi:
            cancellations.append("Mars is conjunct the Moon (Chandra-Mangala yoga).")

    return MangalPerson(
        references=[n for n, _ in refs], hits=hits,
        house_exceptions=exceptions, cancellations=cancellations,
        severity=sum(weights[n] for n, _ in hits))


def saturn_balance(chart: Chart, lagna_known: bool) -> str | None:
    """Dosha samya: Saturn in a Manglik house of the other partner's chart."""
    if lagna_known and chart.lagna_rashi is not None:
        name, ref = "Lagna", chart.lagna_rashi
    else:
        name, ref = "Moon", chart.moon.rashi
    h = (chart.sign("Saturn") - ref) % 12 + 1
    if h in D.MANGLIK_HOUSES:
        return f"Saturn in house {h} from {name}"
    return None


def mangal_findings(people: dict[str, tuple[str, Chart, bool]],
                    sweeps: dict[str, Sweep]) -> list[DoshaFinding]:
    """people: role -> (display name, chart, lagna_known)."""
    analysis = {role: analyse_mangal(ch, lk) for role, (_, ch, lk) in people.items()}
    out = []
    for role, other in (("bride", "groom"), ("groom", "bride")):
        name, chart, lagna_known = people[role]
        m, om = analysis[role], analysis[other]
        f = DoshaFinding(f"mangal_{role}", f"Mangal Dosha: {name}", ABSENT)
        f.details.append("Checked from: " + ", ".join(m.references) + ".")
        if not lagna_known:
            f.details.append("Birth time unknown, so the Lagna was not used.")
        f.details += m.house_exceptions
        if not m.raw:
            f.details.append("Mars is not in houses 1, 2, 4, 7, 8 or 12 from "
                             "any reference point (after exceptions).")
        else:
            f.details.append("Mars in " + ", ".join(
                f"house {h} from {n}" for n, h in m.hits)
                + f" (intensity: {severity_label(m.severity)}).")
            cancels, mitig = list(m.cancellations), []
            if not cancels and om.net:
                cancels.append("Both partners have Mangal Dosha: mutual "
                               "cancellation (the most widely applied rule).")
            if not cancels:
                _, ochart, olk = people[other]
                bal = saturn_balance(ochart, olk)
                if bal:
                    mitig.append(f"Partner has {bal} (dosha samya / balancing).")
            f.status = _status(cancels, mitig)
            f.parihara = cancels + mitig

        sw = sweeps.get(role)
        if sw:
            lagna_varies = (lagna_known and len(
                {h in D.MANGLIK_HOUSES for h in sw.mars_houses_from_lagna}) > 1)
            moon_varies = len({analyse_mangal(alt, lagna_known).net
                               for alt in sw.moon_states}) > 1
            if lagna_varies or moon_varies:
                f.time_sensitive = True
                f.details.append("Within the birth-time window this result "
                                 "changes (the Lagna or Moon moves into a "
                                 "different sign), so it depends on the exact "
                                 "birth time.")
        out.append(f)
    return out


# ---------------------------------------------------------------- full match


@dataclass
class Person:
    name: str
    chart: Chart
    sweep: Sweep
    lagna_known: bool


@dataclass
class MatchResult:
    kootas: list[Koota]
    total: float
    band: str
    doshas: list[DoshaFinding]
    score_min: float
    score_max: float
    sensitivity_notes: list[str]


def _state_list(p: Person) -> str:
    return "; ".join(c.moon.describe() for c in p.sweep.moon_states)


def match(bride: Person, groom: Person) -> MatchResult:
    b, g = bride.chart.moon, groom.chart.moon
    kootas = score_kootas(b, g)
    total = total_score(kootas)

    totals = [total_score(score_kootas(x.moon, y.moon))
              for x, y in product(bride.sweep.moon_states, groom.sweep.moon_states)]

    doshas = [nadi_dosha(b, g), bhakoot_dosha(b, g), gana_dosha(b, g)]
    # Couple-level doshas are time-sensitive if any alternative Moon state changes them.
    for f in doshas:
        fn = {"nadi": nadi_dosha, "bhakoot": bhakoot_dosha, "gana": gana_dosha}[f.key]
        statuses = {fn(x.moon, y.moon).status for x, y in
                    product(bride.sweep.moon_states, groom.sweep.moon_states)}
        if len(statuses) > 1:
            f.time_sensitive = True
            f.details.append("This result changes within the birth-time window "
                             "(a Moon is close to a nakshatra/sign boundary).")

    doshas += mangal_findings(
        {"bride": (bride.name, bride.chart, bride.lagna_known),
         "groom": (groom.name, groom.chart, groom.lagna_known)},
        {"bride": bride.sweep, "groom": groom.sweep})

    notes = []
    for p in (bride, groom):
        if len(p.sweep.moon_states) > 1:
            notes.append(f"{p.name}'s Moon is near a boundary. Within the "
                         f"birth-time window it could be: {_state_list(p)}.")
        if p.lagna_known and len(p.sweep.lagna_signs) > 1:
            signs = ", ".join(D.RASHIS[s] for s in p.sweep.lagna_signs)
            notes.append(f"{p.name}'s Lagna (ascendant) changes within the "
                         f"birth-time window: {signs}.")

    return MatchResult(kootas=kootas, total=total, band=D.score_band(total),
                       doshas=doshas, score_min=min(totals),
                       score_max=max(totals), sensitivity_notes=notes)
