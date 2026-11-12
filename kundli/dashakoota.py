"""Dashakoota (ದಶಕೂಟ): the 10-koota marriage matching used in Karnataka and
the rest of South India.

Each koota is judged Uttama (1), Madhyama (0.5) or Adhama (0), giving a score
out of 10. Rajju and Vedha are treated as critical: tradition strongly
discourages a match where either fails.

Counting is always from the bride's nakshatra / rashi to the groom's, with
the bride's own counted as 1. Rules marked VARIANT differ between almanacs.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import data as D
from .engine import MoonPos
from .i18n import M, Msg, Name
from .matching import maitri_points, relation

UTTAMA, MADHYAMA, ADHAMA = "uttama", "madhyama", "adhama"
POINTS = {UTTAMA: 1.0, MADHYAMA: 0.5, ADHAMA: 0.0}
KEYS = ["dina", "gana", "mahendra", "stree_deergha", "yoni", "rashi",
        "rashyadhipati", "vashya", "rajju", "vedha"]
CRITICAL = {"rajju", "vedha"}

# Rajju groups follow a 1-2-3-4-5-4-3-2-1 pattern through each run of 9 stars.
RAJJU_NAMES = ["pada", "kati", "nabhi", "kantha", "shiro"]
_RAJJU_CYCLE = [0, 1, 2, 3, 4, 3, 2, 1, 0]


def rajju_of(nak: int) -> int:
    return _RAJJU_CYCLE[nak % 9]


# Vedha: mutually obstructing stars (Mrigashira, Chitra, Dhanishta all
# obstruct each other).
_VEDHA_PAIRS = [(0, 17), (1, 16), (2, 15), (3, 14), (5, 21), (6, 20), (7, 19),
                (8, 18), (9, 26), (10, 25), (11, 24), (12, 23),
                (4, 13), (4, 22), (13, 22)]
VEDHA = {frozenset(p) for p in _VEDHA_PAIRS}

# VARIANT. Sign -> signs that are "vashya" to it (classical South Indian table).
VASHYA_SIGNS = {
    0: {4, 7},      # Mesha: Simha, Vrishchika
    1: {3, 6},      # Vrishabha: Karka, Tula
    2: {5},         # Mithuna: Kanya
    3: {7, 8},      # Karka: Vrishchika, Dhanu
    4: {6},         # Simha: Tula
    5: {11, 2},     # Kanya: Meena, Mithuna
    6: {9, 5},      # Tula: Makara, Kanya
    7: {3},         # Vrishchika: Karka
    8: {11},        # Dhanu: Meena
    9: {0, 10},     # Makara: Mesha, Kumbha
    10: {0},        # Kumbha: Mesha
    11: {9},        # Meena: Makara
}


@dataclass
class DKoota:
    key: str
    result: str
    bride: object
    groom: object
    note: Msg | None = None

    @property
    def points(self) -> float:
        return POINTS[self.result]

    @property
    def name(self) -> Name:
        return Name("dk", self.key)


def count(frm: int, to: int, n: int) -> int:
    return (to - frm) % n + 1


def score_dashakoota(b: MoonPos, g: MoonPos) -> list[DKoota]:
    out: list[DKoota] = []
    nb, ng = b.nakshatra, g.nakshatra
    c = count(nb, ng, 27)
    bn, gn = Name("nakshatra", nb), Name("nakshatra", ng)

    # 1. Dina: remainder of the count / 9 is 2, 4, 6, 8 or 0
    out.append(DKoota("dina", UTTAMA if c % 9 in (2, 4, 6, 8, 0) else ADHAMA,
                      bn, gn, M("dk_count_note", n=c)))

    # 2. Gana
    gb, gg = D.NAK_GANA[nb], D.NAK_GANA[ng]
    if gb == gg:
        gres = UTTAMA
    elif {gb, gg} == {0, 1}:
        gres = MADHYAMA
    else:
        gres = ADHAMA
    out.append(DKoota("gana", gres, Name("gana", gb), Name("gana", gg)))

    # 3. Mahendra: count 4, 7, 10, ... 25
    out.append(DKoota("mahendra", UTTAMA if c in (4, 7, 10, 13, 16, 19, 22, 25) else ADHAMA,
                      bn, gn, M("dk_count_note", n=c)))

    # 4. Stree Deergha: groom's star well ahead of the bride's
    sres = UTTAMA if c > 13 else (MADHYAMA if c > 9 else ADHAMA)
    out.append(DKoota("stree_deergha", sres, bn, gn, M("dk_count_note", n=c)))

    # 5. Yoni
    yb, yg = D.NAK_YONI[nb], D.NAK_YONI[ng]
    ys = D.YONI_SCORE[yb][yg]
    yres = UTTAMA if ys >= 3 else (MADHYAMA if ys == 2 else ADHAMA)
    out.append(DKoota("yoni", yres, Name("yoni", yb), Name("yoni", yg)))

    # 6. Rashi (VARIANT): same sign or beyond the 6th is good; 6/8 is avoided;
    # 2/12 needs caution.
    rc = count(b.rashi, g.rashi, 12)
    lb, lg = D.RASHI_LORD[b.rashi], D.RASHI_LORD[g.rashi]
    friendly = lb == lg or maitri_points(lb, lg) == 5.0
    if rc in (1, 7, 9, 10, 11):
        rres = UTTAMA
    elif rc == 12 or (rc in (6, 8, 2) and friendly):
        rres = MADHYAMA
    else:
        rres = ADHAMA
    out.append(DKoota("rashi", rres, Name("rashi", b.rashi), Name("rashi", g.rashi),
                      M("dk_rashi_note", n=rc)))

    # 7. Rashyadhipati: friendship of the Moon-sign lords
    rel = {relation(lb, lg), relation(lg, lb)}
    if lb == lg or rel == {"friend"}:
        ares = UTTAMA
    elif "enemy" in rel:
        ares = ADHAMA
    else:
        ares = MADHYAMA
    out.append(DKoota("rashyadhipati", ares, Name("planet", lb), Name("planet", lg)))

    # 8. Vashya (VARIANT table)
    vres = UTTAMA if (g.rashi in VASHYA_SIGNS[b.rashi]
                      or b.rashi in VASHYA_SIGNS[g.rashi]) else ADHAMA
    out.append(DKoota("vashya", vres, Name("rashi", b.rashi), Name("rashi", g.rashi)))

    # 9. Rajju: must differ
    rb, rg = rajju_of(nb), rajju_of(ng)
    out.append(DKoota("rajju", ADHAMA if rb == rg else UTTAMA,
                      Name("rajju", rb), Name("rajju", rg)))

    # 10. Vedha: must not be an obstructing pair
    out.append(DKoota("vedha", ADHAMA if frozenset((nb, ng)) in VEDHA else UTTAMA,
                      bn, gn))
    return out


def dashakoota_total(kootas: list[DKoota]) -> float:
    return sum(k.points for k in kootas)


def critical_failures(kootas: list[DKoota]) -> list[str]:
    return [k.key for k in kootas if k.key in CRITICAL and k.result == ADHAMA]


def dk_band(total: float, critical: list[str]) -> str:
    if critical:
        return "critical"
    if total >= 7:
        return "good"
    if total >= 5:
        return "average"
    return "weak"
