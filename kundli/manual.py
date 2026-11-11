"""Moon positions when a person's rashi and nakshatra are entered directly.

The zodiac has 108 padas (27 nakshatras x 4), and each rashi holds exactly 9
of them, so pada q (0..107) belongs to nakshatra q // 4 and rashi q // 9.
Working in whole padas avoids any floating-point edge cases.
"""
from __future__ import annotations

from .engine import PADA_SPAN, MoonPos


def nakshatras_in_rashi(rashi: int) -> list[int]:
    return sorted({q // 4 for q in range(9 * rashi, 9 * rashi + 9)})


def padas_in(rashi: int, nakshatra: int) -> list[int]:
    return [q % 4 + 1 for q in range(9 * rashi, 9 * rashi + 9) if q // 4 == nakshatra]


def moon_states_for(rashi: int, nakshatra: int, pada: int | None = None) -> list[MoonPos]:
    """Every distinct Moon state compatible with the entered rashi, nakshatra
    and (optional) pada. The first item is the nominal position (the middle
    of the allowed range)."""
    qs = [q for q in range(9 * rashi, 9 * rashi + 9)
          if q // 4 == nakshatra and (pada is None or q % 4 + 1 == pada)]
    if not qs:
        raise ValueError("That nakshatra/pada is not in that rashi.")
    lo, hi = qs[0] * PADA_SPAN, (qs[-1] + 1) * PADA_SPAN
    nominal = MoonPos((lo + hi) / 2)
    states = {nominal.state_key: nominal}
    x = lo + 0.05
    while x < hi:
        m = MoonPos(x)
        states.setdefault(m.state_key, m)
        x += 0.1
    return list(states.values())
