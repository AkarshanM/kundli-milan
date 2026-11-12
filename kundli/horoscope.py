"""Individual horoscope (kundli): planets, houses, Navamsa, Panchanga,
Avakahada details, Vimshottari Dasha and individual doshas.

Like the matching engine, everything is deterministic and display text is
returned as translatable Msg / Name objects.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import swisseph as swe

from . import data as D
from .engine import NAK_SPAN, PADA_SPAN, Chart, calculate_chart, sunrise_before
from .i18n import M, Msg, Name
from .matching import MangalPerson, Person, analyse_mangal

BODIES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
          "Rahu", "Ketu"]

# Exaltation / debilitation / own signs (classical; Rahu/Ketu omitted
# because traditions disagree).
EXALT = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3,
         "Venus": 11, "Saturn": 6}
OWN = {"Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
       "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10}}

# Vimshottari: lords in order from Ashwini, and their years.
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",
               "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
               "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
YEAR_DAYS = 365.25


def nakshatra_lord(nak: int) -> str:
    return DASHA_ORDER[nak % 9]


def dignity(planet: str, sign: int) -> str | None:
    if planet in EXALT:
        if sign == EXALT[planet]:
            return "exalt"
        if sign == (EXALT[planet] + 6) % 12:
            return "debil"
        if sign in OWN[planet]:
            return "own"
    return None


def navamsa_sign(lon: float) -> int:
    """Each sign has 9 navamsas; counting continues around the zodiac, so the
    navamsa sign is simply the overall pada index mod 12."""
    return int(lon // PADA_SPAN) % 12


# ------------------------------------------------------------------ planets


@dataclass
class PlanetRow:
    name: str
    lon: float
    sign: int
    nakshatra: int
    pada: int
    house: int | None
    retro: bool
    dignity: str | None
    navamsa: int

    @property
    def nak_lord(self) -> str:
        return nakshatra_lord(self.nakshatra)


def planet_rows(chart: Chart) -> list[PlanetRow]:
    lagna = chart.lagna_rashi
    rows = []
    for name in BODIES:
        lon = chart.longitudes[name]
        sign = int(lon // 30) % 12
        rows.append(PlanetRow(
            name=name, lon=lon, sign=sign,
            nakshatra=int(lon // NAK_SPAN) % 27,
            pada=int((lon % NAK_SPAN) // PADA_SPAN) + 1,
            house=None if lagna is None else (sign - lagna) % 12 + 1,
            retro=chart.speeds.get(name, 0.0) < 0 and name not in ("Sun", "Moon"),
            dignity=dignity(name, sign),
            navamsa=navamsa_sign(lon),
        ))
    return rows


# ---------------------------------------------------------------- panchanga


@dataclass
class Panchanga:
    vara: int          # 0 = Sunday ... 6 = Saturday
    tithi: int         # 0..29 (0-14 Shukla Prathama..Purnima, 15-29 Krishna..Amavasya)
    yoga: int          # 0..26
    karana: str        # key into the karana name table
    vara_by_sunrise: bool

    @property
    def paksha(self) -> str:
        return "shukla" if self.tithi < 15 else "krishna"

    @property
    def tithi_in_paksha(self) -> int:
        """0..14 within the paksha (14 = Purnima / Amavasya)."""
        return self.tithi % 15


_MOVABLE_KARANAS = ["bava", "balava", "kaulava", "taitila", "gara", "vanija", "vishti"]


def karana_key(half_tithi: int) -> str:
    if half_tithi == 0:
        return "kimstughna"
    if half_tithi >= 57:
        return ["shakuni", "chatushpada", "naga"][half_tithi - 57]
    return _MOVABLE_KARANAS[(half_tithi - 1) % 7]


def panchanga(chart: Chart, lat: float, lon: float) -> Panchanga:
    sun, moon = chart.longitudes["Sun"], chart.longitudes["Moon"]
    elong = (moon - sun) % 360.0
    tithi = int(elong // 12)
    yoga = int(((sun + moon) % 360.0) // NAK_SPAN)
    karana = karana_key(int(elong // 6))

    # Vara runs from sunrise to sunrise. Date of that sunrise in local mean
    # time (longitude-based) gives the weekday.
    rise = sunrise_before(chart.jd_ut, lat, lon)
    ref = rise if rise is not None else chart.jd_ut
    by_sunrise = rise is not None
    local_jd = ref + lon / 360.0
    # swe.day_of_week: 0 = Monday ... 6 = Sunday  ->  convert to 0 = Sunday
    vara = (swe.day_of_week(local_jd) + 1) % 7
    return Panchanga(vara=vara, tithi=tithi, yoga=yoga, karana=karana,
                     vara_by_sunrise=by_sunrise)


# ------------------------------------------------- Chandramana (Karnataka)


def _elongation(jd: float) -> float:
    sun = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0][0]
    moon = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0][0]
    return (moon - sun) % 360.0


def _refine_new_moon(t: float) -> float:
    for _ in range(8):
        e = _elongation(t)
        if e > 180:
            e -= 360
        t -= e / 12.19          # mean relative speed, deg/day
    return t


def new_moon_before(jd: float) -> float:
    return _refine_new_moon(jd - _elongation(jd) / 12.19)


def new_moon_after(jd: float) -> float:
    return _refine_new_moon(jd + (360.0 - _elongation(jd)) / 12.19)


def _sidereal_sun_sign(jd: float) -> int:
    lon = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]
    return int(lon // 30) % 12


@dataclass
class Chandramana:
    samvatsara: int        # 0 = Prabhava ... 59 = Akshaya
    shaka: int             # Shalivahana Shaka year
    masa: int              # 0 = Chaitra ... 11 = Phalguna (amanta)
    adhika: bool
    ritu: int              # 0 = Vasanta ... 5 = Shishira
    uttarayana: bool
    sunrise: datetime | None
    sunset: datetime | None
    ishtakala: tuple[int, int] | None   # (ghati, vighati) since sunrise


def _jd_to_utc(jd: float) -> datetime:
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    return datetime(y, m, d, tzinfo=timezone.utc) + timedelta(hours=h)


def chandramana(chart: Chart, lat: float, lon: float) -> Chandramana:
    """Karnataka's Chandramana (lunar, amanta) calendar details at birth.
    A month runs from new moon to new moon and is named after the sidereal
    sign the Sun is in when it begins (Sun in Meena -> Chaitra). A month with
    no solar ingress is Adhika. The 60-year samvatsara cycle restarts with
    Prabhava at Ugadi 1987."""
    from .engine import _configure_thread
    _configure_thread()
    jd = chart.jd_ut
    nm1, nm2 = new_moon_before(jd), new_moon_after(jd)
    s1, s2 = _sidereal_sun_sign(nm1), _sidereal_sun_sign(nm2)
    masa = (s1 + 1) % 12
    year_start = _jd_to_utc(nm1 - masa * 29.53)     # around Ugadi of this year
    g = year_start.year

    sun = chart.longitudes["Sun"]
    rise = sunrise_before(jd, lat, lon)
    sunset = None
    ishta = None
    if rise is not None:
        res, tret = swe.rise_trans(rise, swe.SUN, swe.CALC_SET | swe.BIT_HINDU_RISING,
                                   (lon, lat, 0.0))
        if res == 0:
            sunset = _jd_to_utc(tret[0])
        ghatis = (jd - rise) * 60.0
        gh = int(ghatis)
        vg = int(round((ghatis - gh) * 60))
        if vg == 60:
            gh, vg = gh + 1, 0
        ishta = (gh, vg)

    return Chandramana(
        samvatsara=(g - 1987) % 60,
        shaka=g - 78,
        masa=masa,
        adhika=(s1 == s2),
        ritu=masa // 2,
        uttarayana=(sun >= 270.0 or sun < 90.0),
        sunrise=_jd_to_utc(rise) if rise is not None else None,
        sunset=sunset,
        ishtakala=ishta,
    )


# -------------------------------------------------------------------- dasha


@dataclass
class DashaPeriod:
    lord: str
    start: datetime
    end: datetime
    sub: list["DashaPeriod"] = field(default_factory=list)

    def contains(self, when: datetime) -> bool:
        return self.start <= when < self.end


def _antardashas(md: DashaPeriod) -> list[DashaPeriod]:
    total_days = (md.end - md.start).total_seconds() / 86400
    i = DASHA_ORDER.index(md.lord)
    out, t = [], md.start
    for k in range(9):
        lord = DASHA_ORDER[(i + k) % 9]
        # AD length = MD length * AD years / 120
        days = total_days * DASHA_YEARS[lord] / 120
        end = t + timedelta(days=days)
        out.append(DashaPeriod(lord, t, end))
        t = end
    out[-1].end = md.end      # absorb rounding
    return out


def vimshottari(moon_lon: float, birth_utc: datetime, years_ahead: float = 120.0) -> list[DashaPeriod]:
    nak = int(moon_lon // NAK_SPAN) % 27
    lord = nakshatra_lord(nak)
    fraction_left = 1.0 - (moon_lon % NAK_SPAN) / NAK_SPAN
    first_years = DASHA_YEARS[lord] * fraction_left
    # The first Mahadasha began before birth; record its true start so that
    # its Antardashas line up correctly.
    full_days = DASHA_YEARS[lord] * YEAR_DAYS
    start = birth_utc - timedelta(days=full_days - first_years * YEAR_DAYS)
    limit = birth_utc + timedelta(days=years_ahead * YEAR_DAYS)
    periods, i = [], DASHA_ORDER.index(lord)
    t = start
    while t < limit:
        l = DASHA_ORDER[i % 9]
        end = t + timedelta(days=DASHA_YEARS[l] * YEAR_DAYS)
        md = DashaPeriod(l, t, end)
        md.sub = _antardashas(md)
        periods.append(md)
        t, i = end, i + 1
    return periods


def dasha_balance(moon_lon: float) -> tuple[str, int, int, int]:
    """(lord, years, months, days) remaining at birth."""
    nak = int(moon_lon // NAK_SPAN) % 27
    lord = nakshatra_lord(nak)
    years = DASHA_YEARS[lord] * (1.0 - (moon_lon % NAK_SPAN) / NAK_SPAN)
    y = int(years)
    months_f = (years - y) * 12
    m = int(months_f)
    d = int(round((months_f - m) * 30))
    if d == 30:
        m, d = m + 1, 0
    if m == 12:
        y, m = y + 1, 0
    return lord, y, m, d


# ------------------------------------------------------------------- doshas


def kaal_sarpa(chart: Chart) -> bool:
    """All seven planets on one side of the Rahu-Ketu axis."""
    rahu = chart.longitudes["Rahu"]
    sides = {((chart.longitudes[p] - rahu) % 360.0) < 180.0
             for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")}
    return len(sides) == 1


def sade_sati_phase(natal_moon_sign: int, saturn_sign_now: int) -> int | None:
    """1 = rising (12th from Moon), 2 = peak (over Moon), 3 = setting (2nd)."""
    h = (saturn_sign_now - natal_moon_sign) % 12 + 1
    return {12: 1, 1: 2, 2: 3}.get(h)


# --------------------------------------------------------------- horoscope


@dataclass
class Horoscope:
    person: Person
    planets: list[PlanetRow]
    lagna_sign: int
    lagna_lon: float
    lagna_navamsa: int
    panchanga: Panchanga
    dashas: list[DashaPeriod]
    balance: tuple[str, int, int, int]
    mangal: MangalPerson
    kaal_sarpa: bool
    sade_sati: int | None
    saturn_now: int
    computed_at: datetime
    notes: list[Msg]
    utc_offset: timedelta = timedelta(0)   # for showing dates in local time
    chandramana: Chandramana | None = None

    def local_date(self, when: datetime) -> str:
        return (when + self.utc_offset).strftime("%Y-%m-%d")

    def local_time(self, when: datetime | None) -> str:
        return "" if when is None else (when + self.utc_offset).strftime("%H:%M")

    @property
    def chart(self) -> Chart:
        return self.person.chart

    def current_dasha(self) -> tuple[DashaPeriod | None, DashaPeriod | None]:
        for md in self.dashas:
            if md.contains(self.computed_at):
                for ad in md.sub:
                    if ad.contains(self.computed_at):
                        return md, ad
                return md, None
        return None, None


def build_horoscope(person: Person, lat: float, lon: float,
                    now: datetime | None = None,
                    utc_offset: timedelta = timedelta(0)) -> Horoscope:
    chart = person.chart
    if chart is None or chart.lagna_lon is None:
        raise ValueError("A full kundli needs birth date, time and place.")
    now = now or datetime.now(timezone.utc)
    saturn_now = calculate_chart(now, lat, lon, with_lagna=False).sign("Saturn")
    moon = chart.longitudes["Moon"]

    notes: list[Msg] = []
    sw = person.sweep
    if sw and len(sw.lagna_signs) > 1:
        notes.append(M("note_lagna_changes", name=person.name,
                       signs=_join_rashis(sw.lagna_signs)))
    if len(person.moon_states) > 1:
        from .i18n import Join
        notes.append(M("note_moon_boundary", name=person.name, states=Join(
            [m.describe() for m in person.moon_states], "; ")))

    return Horoscope(
        person=person,
        planets=planet_rows(chart),
        lagna_sign=chart.lagna_rashi,
        lagna_lon=chart.lagna_lon,
        lagna_navamsa=navamsa_sign(chart.lagna_lon),
        panchanga=panchanga(chart, lat, lon),
        dashas=vimshottari(moon, chart.utc),
        balance=dasha_balance(moon),
        mangal=analyse_mangal(chart, lagna_known=True),
        kaal_sarpa=kaal_sarpa(chart),
        sade_sati=sade_sati_phase(chart.moon.rashi, saturn_now),
        saturn_now=saturn_now,
        computed_at=now,
        notes=notes,
        utc_offset=utc_offset,
        chandramana=chandramana(chart, lat, lon),
    )


def _join_rashis(signs):
    from .i18n import Join
    return Join([Name("rashi", s) for s in signs])
