"""Astronomical calculations, using Swiss Ephemeris (pyswisseph).

All longitudes are sidereal (Lahiri / Chitrapaksha ayanamsa).
If the Swiss Ephemeris data files are present in ./ephe they are used;
otherwise Swiss Ephemeris falls back to its built-in Moshier model, which is
accurate to a few arc-seconds -- far finer than a nakshatra pada (3 deg 20').
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import swisseph as swe

from . import data as D

EPHE_DIR = Path(__file__).resolve().parent.parent / "ephe"

# Swiss Ephemeris keeps its settings in thread-local storage. Streamlit runs
# every page in a worker thread, so a setting made once at import time would
# NOT apply there (it would silently fall back to the Fagan-Bradley
# ayanamsa). Configure each thread before its first calculation.
_thread_state = threading.local()


def _configure_thread() -> None:
    if getattr(_thread_state, "ready", False):
        return
    swe.set_ephe_path(str(EPHE_DIR))
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    _thread_state.ready = True

NAK_SPAN = 360.0 / 27.0
PADA_SPAN = NAK_SPAN / 4.0

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}


@dataclass(frozen=True)
class MoonPos:
    lon: float  # sidereal longitude, degrees

    @property
    def nakshatra(self) -> int:
        return int(self.lon // NAK_SPAN) % 27

    @property
    def pada(self) -> int:
        return int((self.lon % NAK_SPAN) // PADA_SPAN) + 1

    @property
    def rashi(self) -> int:
        return int(self.lon // 30) % 12

    @property
    def vashya(self) -> int:
        return D.vashya_class(self.lon)

    @property
    def state_key(self) -> tuple:
        """Everything Ashtakoota depends on. Two positions with the same key
        produce identical koota scores."""
        return (self.nakshatra, self.pada, self.rashi, self.vashya)

    def describe(self) -> str:
        return (f"{D.NAKSHATRAS[self.nakshatra]} pada {self.pada}, "
                f"{D.RASHIS[self.rashi]}")


@dataclass
class Chart:
    utc: datetime | None
    jd_ut: float
    longitudes: dict[str, float]          # sidereal, includes Ketu
    lagna_lon: float | None               # None when birth time is unknown
    ayanamsa: float
    ephemeris: str

    @property
    def moon(self) -> MoonPos:
        return MoonPos(self.longitudes["Moon"])

    @property
    def lagna_rashi(self) -> int | None:
        return None if self.lagna_lon is None else int(self.lagna_lon // 30) % 12

    def sign(self, planet: str) -> int:
        return int(self.longitudes[planet] // 30) % 12


def julian_day(utc: datetime) -> float:
    utc = utc.astimezone(timezone.utc)
    hour = (utc.hour + utc.minute / 60 + utc.second / 3600
            + utc.microsecond / 3.6e9)
    return swe.julday(utc.year, utc.month, utc.day, hour, swe.GREG_CAL)


def calculate_chart(utc: datetime, lat: float, lon: float,
                    with_lagna: bool = True) -> Chart:
    _configure_thread()
    jd = julian_day(utc)
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    longitudes: dict[str, float] = {}
    ephemeris = "Swiss Ephemeris data files"
    for name, pid in PLANETS.items():
        xx, retflag = swe.calc_ut(jd, pid, flags)
        if not retflag & swe.FLG_SWIEPH:
            ephemeris = "Swiss Ephemeris (built-in Moshier model)"
        longitudes[name] = xx[0] % 360.0
    longitudes["Ketu"] = (longitudes["Rahu"] + 180.0) % 360.0

    lagna = None
    if with_lagna:
        _cusps, ascmc = swe.houses_ex(jd, lat, lon, b"W", swe.FLG_SIDEREAL)
        lagna = ascmc[0] % 360.0

    return Chart(
        utc=utc.astimezone(timezone.utc),
        jd_ut=jd,
        longitudes=longitudes,
        lagna_lon=lagna,
        ayanamsa=swe.get_ayanamsa_ut(jd),
        ephemeris=ephemeris,
    )


def tropical_longitude(utc: datetime, planet: str) -> float:
    """Tropical (non-sidereal) longitude; used by self-tests only."""
    _configure_thread()
    xx, _ = swe.calc_ut(julian_day(utc), PLANETS[planet], swe.FLG_SWIEPH)
    return xx[0] % 360.0


# --------------------------------------------------------------------------
# Birth-time sensitivity sweep
# --------------------------------------------------------------------------
# Minutes either side of the stated time that we test, by declared accuracy.
ACCURACY_WINDOWS = {"exact": 5, "approx_15m": 15, "approx_1h": 60}


@dataclass
class Sweep:
    moon_states: list[Chart] = field(default_factory=list)  # one per distinct Moon state
    lagna_signs: list[int] = field(default_factory=list)
    mars_houses_from_lagna: list[int] = field(default_factory=list)
    start_utc: datetime | None = None
    end_utc: datetime | None = None


def sweep(nominal: Chart, start_utc: datetime, end_utc: datetime,
          lat: float, lon: float, with_lagna: bool,
          step_minutes: int = 2) -> Sweep:
    """Recalculate the chart every few minutes across the window and record
    every distinct Moon state, Lagna sign and Mars-from-Lagna house."""
    states: dict[tuple, Chart] = {nominal.moon.state_key: nominal}
    lagnas: list[int] = []
    mars_houses: list[int] = []

    def record(ch: Chart) -> None:
        states.setdefault(ch.moon.state_key, ch)
        if ch.lagna_rashi is not None:
            if ch.lagna_rashi not in lagnas:
                lagnas.append(ch.lagna_rashi)
            h = (ch.sign("Mars") - ch.lagna_rashi) % 12 + 1
            if h not in mars_houses:
                mars_houses.append(h)

    record(nominal)
    t = start_utc
    step = timedelta(minutes=step_minutes)
    while t <= end_utc:
        record(calculate_chart(t, lat, lon, with_lagna))
        t += step
    record(calculate_chart(end_utc, lat, lon, with_lagna))

    return Sweep(
        moon_states=list(states.values()),
        lagna_signs=lagnas,
        mars_houses_from_lagna=mars_houses,
        start_utc=start_utc,
        end_utc=end_utc,
    )
