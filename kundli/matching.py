"""Ashtakoota scoring, dosha detection and cancellation (parihara) rules.

Everything here is deterministic. The AI layer only ever explains the output
of this module; it never computes anything. Display text is returned as
language-neutral `Msg` / `Name` objects (see i18n.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product

from . import data as D
from .engine import Chart, MoonPos, Sweep
from .i18n import Join, M, Msg, Name

# ---------------------------------------------------------------- kootas


@dataclass
class Koota:
    key: str
    score: float
    max: float
    bride: object          # Name or Msg
    groom: object
    note: Msg | None = None

    @property
    def name(self) -> Name:
        return Name("koota", self.key)


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


def _yoni(nak: int) -> Msg:
    return M("yoni_value", animal=Name("yoni", D.NAK_YONI[nak]),
             sex=Name("sex", D.NAK_YONI_GENDER[nak]))


def _P(planet: str) -> Name:
    return Name("planet", planet)


def score_kootas(b: MoonPos, g: MoonPos) -> list[Koota]:
    out: list[Koota] = []

    vb, vg = D.RASHI_VARNA[b.rashi], D.RASHI_VARNA[g.rashi]
    out.append(Koota("varna", 1.0 if vg >= vb else 0.0, 1,
                     Name("varna", vb), Name("varna", vg)))

    cb, cg = b.vashya, g.vashya
    out.append(Koota("vashya", D.VASHYA_SCORE[cg][cb], 2,
                     Name("vashya", cb), Name("vashya", cg)))

    c_bg = tara_count(b.nakshatra, g.nakshatra)
    c_gb = tara_count(g.nakshatra, b.nakshatra)
    out.append(Koota(
        "tara", 1.5 * tara_good(c_bg) + 1.5 * tara_good(c_gb), 3,
        M("tara_value_bride", tara=Name("tara", c_bg % 9), n=c_bg),
        M("tara_value_groom", tara=Name("tara", c_gb % 9), n=c_gb),
        M("tara_note")))

    yb, yg = D.NAK_YONI[b.nakshatra], D.NAK_YONI[g.nakshatra]
    out.append(Koota("yoni", float(D.YONI_SCORE[yb][yg]), 4,
                     _yoni(b.nakshatra), _yoni(g.nakshatra)))

    lb, lg = D.RASHI_LORD[b.rashi], D.RASHI_LORD[g.rashi]
    out.append(Koota(
        "maitri", maitri_points(lb, lg), 5,
        M("maitri_value", lord=_P(lb), rashi=Name("rashi", b.rashi)),
        M("maitri_value", lord=_P(lg), rashi=Name("rashi", g.rashi)),
        M("maitri_note", a=_P(lb), b=_P(lg),
          rel_ab=Name("rel", relation(lb, lg)),
          rel_ba=Name("rel", relation(lg, lb)))))

    gb, gg = D.NAK_GANA[b.nakshatra], D.NAK_GANA[g.nakshatra]
    out.append(Koota("gana", D.GANA_SCORE[gg][gb], 6,
                     Name("gana", gb), Name("gana", gg)))

    d = bhakoot_distance(b.rashi, g.rashi)
    out.append(Koota("bhakoot", 0.0 if d in D.BAD_BHAKOOT else 7.0, 7,
                     Name("rashi", b.rashi), Name("rashi", g.rashi),
                     M("bhakoot_note", label=D.BHAKOOT_LABEL[d])))

    nb, ng = D.nadi_of(b.nakshatra), D.nadi_of(g.nakshatra)
    out.append(Koota("nadi", 0.0 if nb == ng else 8.0, 8,
                     Name("nadi", nb), Name("nadi", ng)))
    return out


def total_score(kootas: list[Koota]) -> float:
    return sum(k.score for k in kootas)


# ---------------------------------------------------------------- doshas

ABSENT, PRESENT, MITIGATED, CANCELLED = "Absent", "Present", "Mitigated", "Cancelled"
NOT_CHECKED = "NotChecked"


@dataclass
class DoshaFinding:
    key: str
    title: Msg
    status: str
    details: list[Msg] = field(default_factory=list)
    parihara: list[Msg] = field(default_factory=list)   # cancellation rules applied
    time_sensitive: bool = False


def _status(cancels: list, mitigations: list) -> str:
    if cancels:
        return CANCELLED
    if mitigations:
        return MITIGATED
    return PRESENT


def nadi_dosha(b: MoonPos, g: MoonPos) -> DoshaFinding:
    nb, ng = D.nadi_of(b.nakshatra), D.nadi_of(g.nakshatra)
    f = DoshaFinding("nadi", M("dosha_nadi"), ABSENT)
    if nb != ng:
        f.details.append(M("nadi_different", b=Name("nadi", nb), g=Name("nadi", ng)))
        return f
    f.details.append(M("nadi_same", nadi=Name("nadi", nb)))
    cancels, mitig = [], []
    lb, lg = D.RASHI_LORD[b.rashi], D.RASHI_LORD[g.rashi]
    if b.rashi == g.rashi and b.nakshatra != g.nakshatra:
        cancels.append(M("nadi_ph_same_rashi"))
    elif b.nakshatra == g.nakshatra and b.rashi != g.rashi:
        cancels.append(M("nadi_ph_same_nak"))
    elif b.nakshatra == g.nakshatra and b.pada != g.pada:
        mitig.append(M("nadi_ph_diff_pada"))
    if b.nakshatra == g.nakshatra and b.pada == g.pada:
        f.details.append(M("nadi_same_pada"))
    if not cancels and lb != lg and relation(lb, lg) == "friend" and relation(lg, lb) == "friend":
        mitig.append(M("nadi_ph_lords_friends", a=_P(lb), b=_P(lg)))
    f.status = _status(cancels, mitig)
    f.parihara = cancels + mitig
    return f


def bhakoot_dosha(b: MoonPos, g: MoonPos) -> DoshaFinding:
    d = bhakoot_distance(b.rashi, g.rashi)
    label = D.BHAKOOT_LABEL[d]
    f = DoshaFinding("bhakoot", M("dosha_bhakoot"), ABSENT)
    if d not in D.BAD_BHAKOOT:
        f.details.append(M("bhakoot_ok", label=label))
        return f
    f.details.append(M("bhakoot_bad", label=label))
    if label == "5/9":
        f.details.append(M("bhakoot_59_mild"))
    lb, lg = D.RASHI_LORD[b.rashi], D.RASHI_LORD[g.rashi]
    pts = maitri_points(lb, lg)
    cancels, mitig = [], []
    if lb == lg:
        cancels.append(M("bhakoot_ph_same_lord", lord=_P(lb)))
    elif pts == 5.0:
        cancels.append(M("bhakoot_ph_friends", a=_P(lb), b=_P(lg)))
    elif pts == 4.0:
        mitig.append(M("bhakoot_ph_half", a=_P(lb), b=_P(lg)))
    f.status = _status(cancels, mitig)
    f.parihara = cancels + mitig
    return f


def gana_dosha(b: MoonPos, g: MoonPos) -> DoshaFinding:
    gb, gg = D.NAK_GANA[b.nakshatra], D.NAK_GANA[g.nakshatra]
    pts = D.GANA_SCORE[gg][gb]
    f = DoshaFinding("gana", M("dosha_gana"), ABSENT)
    if pts > 1:
        f.details.append(M("gana_ok", b=Name("gana", gb), g=Name("gana", gg)))
        return f
    f.details.append(M("gana_bad", b=Name("gana", gb), g=Name("gana", gg), pts=pts))
    lb, lg = D.RASHI_LORD[b.rashi], D.RASHI_LORD[g.rashi]
    maitri = maitri_points(lb, lg)
    cancels, mitig = [], []
    if maitri == 5.0:
        cancels.append(M("gana_ph_lords"))
    elif maitri == 4.0:
        mitig.append(M("gana_ph_lords_half"))
    if bhakoot_distance(b.rashi, g.rashi) not in D.BAD_BHAKOOT:
        mitig.append(M("gana_ph_bhakoot"))
    f.status = _status(cancels, mitig)
    f.parihara = cancels + mitig
    return f


# ------------------------------------------------------------ Mangal Dosha


@dataclass
class MangalPerson:
    references: list[str]
    hits: list[tuple[str, int]]
    house_exceptions: list[Msg]
    cancellations: list[Msg]
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
            exceptions.append(M("mangal_exception", ref=_P(name), house=house,
                                sign=Name("rashi", mars)))
        else:
            hits.append((name, house))

    cancellations: list[Msg] = []
    if hits:
        if mars in D.MARS_OWN_OR_EXALTED:
            cancellations.append(M("mangal_ph_own", sign=Name("rashi", mars),
                                   kind=Name("dignity", D.MARS_OWN_OR_EXALTED[mars])))
        rel = (mars - chart.sign("Jupiter")) % 12 + 1
        if rel == 1:
            cancellations.append(M("mangal_ph_jup_conj"))
        elif rel in (5, 7, 9):
            cancellations.append(M("mangal_ph_jup_aspect", rel=rel))
        if mars == chart.moon.rashi:
            cancellations.append(M("mangal_ph_moon_conj"))

    return MangalPerson(
        references=[n for n, _ in refs], hits=hits,
        house_exceptions=exceptions, cancellations=cancellations,
        severity=sum(weights[n] for n, _ in hits))


def saturn_balance(chart: Chart, lagna_known: bool) -> Msg | None:
    """Dosha samya: Saturn in a Manglik house of the other partner's chart."""
    if lagna_known and chart.lagna_rashi is not None:
        name, ref = "Lagna", chart.lagna_rashi
    else:
        name, ref = "Moon", chart.moon.rashi
    h = (chart.sign("Saturn") - ref) % 12 + 1
    if h in D.MANGLIK_HOUSES:
        return M("mangal_ph_saturn", house=h, ref=_P(name))
    return None


def mangal_findings(people: dict[str, "Person"]) -> list[DoshaFinding]:
    """people: role -> Person. A person entered as rashi/nakshatra has no
    chart; their Manglik status is whatever was declared (or unknown)."""
    analysis = {role: analyse_mangal(p.chart, p.lagna_known) if p.chart else None
                for role, p in people.items()}

    def net(role: str) -> bool | None:
        a = analysis[role]
        return a.net if a else people[role].manglik_declared

    out = []
    for role, other in (("bride", "groom"), ("groom", "bride")):
        p, op = people[role], people[other]
        m = analysis[role]
        f = DoshaFinding(f"mangal_{role}", M("dosha_mangal", name=p.name), ABSENT)

        if m is None:   # entered as rashi / nakshatra: nothing to calculate
            if p.manglik_declared is None:
                f.status = NOT_CHECKED
                f.details.append(M("mangal_not_checked"))
            elif not p.manglik_declared:
                f.details.append(M("mangal_declared_no"))
            else:
                f.details.append(M("mangal_declared_yes"))
                cancels, mitig = [], []
                if net(other):
                    cancels.append(M("mangal_ph_mutual"))
                elif op.chart is not None:
                    bal = saturn_balance(op.chart, op.lagna_known)
                    if bal:
                        mitig.append(bal)
                f.status = _status(cancels, mitig)
                f.parihara = cancels + mitig
            out.append(f)
            continue

        f.details.append(M("mangal_checked",
                           refs=Join([_P(r) for r in m.references])))
        if not p.lagna_known:
            f.details.append(M("mangal_no_lagna"))
        f.details += m.house_exceptions
        if not m.raw:
            f.details.append(M("mangal_absent"))
        else:
            f.details.append(M(
                "mangal_hits",
                hits=Join([M("mangal_hit", house=h, ref=_P(n)) for n, h in m.hits]),
                sev=Name("severity", severity_label(m.severity))))
            cancels, mitig = list(m.cancellations), []
            if not cancels and net(other):
                cancels.append(M("mangal_ph_mutual"))
            if not cancels and op.chart is not None:
                bal = saturn_balance(op.chart, op.lagna_known)
                if bal:
                    mitig.append(bal)
            f.status = _status(cancels, mitig)
            f.parihara = cancels + mitig

        sw = p.sweep
        if sw:
            lagna_varies = (p.lagna_known and len(
                {h in D.MANGLIK_HOUSES for h in sw.mars_houses_from_lagna}) > 1)
            moon_varies = len({analyse_mangal(alt, p.lagna_known).net
                               for alt in sw.moon_states}) > 1
            if lagna_varies or moon_varies:
                f.time_sensitive = True
                f.details.append(M("mangal_time_sensitive"))
        out.append(f)
    return out


# ---------------------------------------------------------------- full match


@dataclass
class Person:
    """Either calculated from birth details (chart + sweep) or entered
    directly as rashi / nakshatra (moon_states only)."""
    name: str
    moon_states: list[MoonPos]              # first item is the nominal position
    chart: Chart | None = None
    sweep: Sweep | None = None
    lagna_known: bool = False
    manglik_declared: bool | None = None    # only for rashi/nakshatra entry
    entered: tuple | None = None            # (rashi, nakshatra, pada|None)

    @property
    def moon(self) -> MoonPos:
        return self.moon_states[0]

    @classmethod
    def from_chart(cls, name: str, chart: Chart, sweep: Sweep,
                   lagna_known: bool) -> "Person":
        return cls(name, [c.moon for c in sweep.moon_states], chart, sweep,
                   lagna_known)

    @classmethod
    def from_rashi_nakshatra(cls, name: str, rashi: int, nakshatra: int,
                             pada: int | None,
                             manglik: bool | None) -> "Person":
        from .manual import moon_states_for
        return cls(name, moon_states_for(rashi, nakshatra, pada),
                   manglik_declared=manglik, entered=(rashi, nakshatra, pada))


@dataclass
class MatchResult:
    kootas: list[Koota]
    total: float
    band: int
    doshas: list[DoshaFinding]
    score_min: float
    score_max: float
    sensitivity_notes: list[Msg]
    # Dashakoota (Karnataka / South Indian 10-koota system)
    dk: list = field(default_factory=list)
    dk_total: float = 0.0
    dk_min: float = 0.0
    dk_max: float = 0.0
    dk_band: str = ""


def rajju_dosha(b: MoonPos, g: MoonPos) -> DoshaFinding:
    from .dashakoota import rajju_of
    rb, rg = rajju_of(b.nakshatra), rajju_of(g.nakshatra)
    f = DoshaFinding("rajju", M("dosha_rajju"), ABSENT)
    if rb != rg:
        f.details.append(M("rajju_diff", b=Name("rajju", rb), g=Name("rajju", rg)))
    else:
        f.status = PRESENT
        f.details.append(M("rajju_same", rajju=Name("rajju", rb)))
        f.details.append(M("rajju_note"))
    return f


def vedha_dosha(b: MoonPos, g: MoonPos) -> DoshaFinding:
    from .dashakoota import VEDHA
    bn, gn = Name("nakshatra", b.nakshatra), Name("nakshatra", g.nakshatra)
    f = DoshaFinding("vedha", M("dosha_vedha"), ABSENT)
    if frozenset((b.nakshatra, g.nakshatra)) in VEDHA:
        f.status = PRESENT
        f.details.append(M("vedha_yes", b=bn, g=gn))
    else:
        f.details.append(M("vedha_no", b=bn, g=gn))
    return f


def match(bride: Person, groom: Person) -> MatchResult:
    b, g = bride.moon, groom.moon
    kootas = score_kootas(b, g)
    total = total_score(kootas)

    combos = list(product(bride.moon_states, groom.moon_states))
    totals = [total_score(score_kootas(x, y)) for x, y in combos]

    from .dashakoota import (critical_failures, dashakoota_total, dk_band,
                             score_dashakoota)
    dk = score_dashakoota(b, g)
    dk_totals = [dashakoota_total(score_dashakoota(x, y)) for x, y in combos]

    doshas = [nadi_dosha(b, g), bhakoot_dosha(b, g), gana_dosha(b, g),
              rajju_dosha(b, g), vedha_dosha(b, g)]
    # Couple-level doshas are sensitive if any alternative Moon state changes them.
    for f in doshas:
        fn = {"nadi": nadi_dosha, "bhakoot": bhakoot_dosha, "gana": gana_dosha,
              "rajju": rajju_dosha, "vedha": vedha_dosha}[f.key]
        if len({fn(x, y).status for x, y in combos}) > 1:
            f.time_sensitive = True
            f.details.append(M("couple_time_sensitive"))

    doshas += mangal_findings({"bride": bride, "groom": groom})

    notes: list[Msg] = []
    for p in (bride, groom):
        if p.chart is None:
            # Entered directly: only flag what the user didn't pin down
            # beyond the pada (e.g. which half of Dhanu / Makara for Vashya).
            if len({(m.nakshatra, m.rashi, m.vashya) for m in p.moon_states}) > 1:
                notes.append(M("note_manual_uncertain", name=p.name, states=Join(
                    [Name("vashya", v) for v in
                     dict.fromkeys(m.vashya for m in p.moon_states)], " / ")))
            continue
        if len(p.moon_states) > 1:
            notes.append(M("note_moon_boundary", name=p.name, states=Join(
                [m.describe() for m in p.moon_states], "; ")))
        if p.lagna_known and len(p.sweep.lagna_signs) > 1:
            notes.append(M("note_lagna_changes", name=p.name, signs=Join(
                [Name("rashi", s) for s in p.sweep.lagna_signs])))

    dk_tot = dashakoota_total(dk)
    return MatchResult(kootas=kootas, total=total, band=D.score_band(total),
                       doshas=doshas, score_min=min(totals),
                       score_max=max(totals), sensitivity_notes=notes,
                       dk=dk, dk_total=dk_tot, dk_min=min(dk_totals),
                       dk_max=max(dk_totals),
                       dk_band=dk_band(dk_tot, critical_failures(dk)))
