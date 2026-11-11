from datetime import date, datetime, time, timedelta, timezone

import pytest

from kundli import data as D
from kundli.engine import NAK_SPAN, Chart, MoonPos, calculate_chart, tropical_longitude
from kundli.matching import (ABSENT, CANCELLED, PRESENT, analyse_mangal,
                             bhakoot_dosha, maitri_points, nadi_dosha,
                             score_kootas, total_score)
from kundli.places import resolve_local_time


def moon_at(nak: int, pada: int = 1, rashi_hint: int | None = None) -> MoonPos:
    """Moon position in the middle of the given nakshatra pada."""
    lon = nak * NAK_SPAN + (pada - 0.5) * NAK_SPAN / 4
    m = MoonPos(lon)
    if rashi_hint is not None:
        assert m.rashi == rashi_hint
    return m


# ------------------------------------------------------------- table sanity
def test_tables_have_27_nakshatras():
    for table in (D.NAK_YONI, D.NAK_GANA):
        assert len(table) == 27
    assert len(D.NAK_YONI_GENDER) == 27


def test_each_gana_and_nadi_has_nine_nakshatras():
    for g in range(3):
        assert D.NAK_GANA.count(g) == 9
    nadis = [D.nadi_of(n) for n in range(27)]
    for n in range(3):
        assert nadis.count(n) == 9


def test_yoni_matrix_symmetric_and_sworn_enemies_zero():
    for i in range(14):
        assert D.YONI_SCORE[i][i] == 4
        for j in range(14):
            assert D.YONI_SCORE[i][j] == D.YONI_SCORE[j][i]
    for a, b in D.SWORN_ENEMY_YONIS:
        assert D.YONI_SCORE[D.YONI_ANIMALS.index(a)][D.YONI_ANIMALS.index(b)] == 0


def test_known_nadi_assignments():
    assert D.nadi_of(0) == 0    # Ashwini - Aadi
    assert D.nadi_of(1) == 1    # Bharani - Madhya
    assert D.nadi_of(2) == 2    # Krittika - Antya
    assert D.nadi_of(26) == 2   # Revati - Antya
    assert D.nadi_of(24) == 0   # Purva Bhadrapada - Aadi


# ------------------------------------------------------------------ kootas
def test_same_nakshatra_scores_28():
    m = moon_at(3)  # Rohini
    ks = {k.key: k.score for k in score_kootas(m, m)}
    assert ks == {"varna": 1, "vashya": 2, "tara": 3, "yoni": 4, "maitri": 5,
                  "gana": 6, "bhakoot": 7, "nadi": 0}
    assert total_score(score_kootas(m, m)) == 28


def test_tara_vipat_one_direction():
    b, g = moon_at(0), moon_at(2)   # count 3 (Vipat) one way, 26 (Mitra) the other
    tara = next(k for k in score_kootas(b, g) if k.key == "tara")
    assert tara.score == 1.5


def test_bhakoot_6_8_is_zero():
    b = MoonPos(15.0)              # Aries
    g = MoonPos(7 * 30 + 15.0)     # Scorpio: 8th from Aries
    bh = next(k for k in score_kootas(b, g) if k.key == "bhakoot")
    assert bh.score == 0
    f = bhakoot_dosha(b, g)
    assert f.status == CANCELLED   # both signs ruled by Mars


def test_maitri_points():
    assert maitri_points("Mars", "Mars") == 5
    assert maitri_points("Sun", "Moon") == 5      # mutual friends
    assert maitri_points("Sun", "Saturn") == 0    # mutual enemies
    assert maitri_points("Moon", "Mercury") == 1  # friend / enemy


def test_varna_groom_lower_scores_zero():
    b = MoonPos(3 * 30 + 5)   # Cancer - Brahmin
    g = MoonPos(2 * 30 + 5)   # Gemini - Shudra
    varna = next(k for k in score_kootas(b, g) if k.key == "varna")
    assert varna.score == 0
    varna_rev = next(k for k in score_kootas(g, b) if k.key == "varna")
    assert varna_rev.score == 1


def test_vashya_split_signs():
    assert D.vashya_class(8 * 30 + 10) == D.MANAVA
    assert D.vashya_class(8 * 30 + 20) == D.CHATUSHPADA
    assert D.vashya_class(9 * 30 + 10) == D.CHATUSHPADA
    assert D.vashya_class(9 * 30 + 20) == D.JALACHARA


# ------------------------------------------------------------------- doshas
def test_nadi_cancel_same_rashi_different_nakshatra():
    b = MoonPos(1.0)          # Ashwini, Aries  (Aadi)
    g = MoonPos(27.0)         # Krittika pada 1, Aries (Antya) - different nadi
    assert nadi_dosha(b, g).status == ABSENT
    # Ardra (Aadi) and Punarvasu (Aadi) in Gemini: same nadi, same rashi
    b = MoonPos(2 * 30 + 10)  # Ardra
    g = MoonPos(2 * 30 + 25)  # Punarvasu
    assert D.nadi_of(b.nakshatra) == D.nadi_of(g.nakshatra)
    assert nadi_dosha(b, g).status == CANCELLED


def test_nadi_same_nakshatra_same_pada_no_cancellation():
    m = moon_at(3, 2)
    assert nadi_dosha(m, m).status == PRESENT


def _chart(**signs) -> Chart:
    lons = {p: 15.0 for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
                              "Venus", "Saturn", "Rahu", "Ketu")}
    for p, s in signs.items():
        if p != "Lagna":
            lons[p] = s * 30 + 15.0
    return Chart(utc=None, jd_ut=0, longitudes=lons,
                 lagna_lon=signs.get("Lagna", 0) * 30 + 15.0,
                 ayanamsa=0, ephemeris="test")


def test_mangal_from_lagna_seventh_house():
    # Lagna Aries, Mars in Libra = 7th. Moon/Venus in Gemini (Mars 5th: no).
    ch = _chart(Lagna=0, Mars=6, Moon=2, Venus=2, Jupiter=1, Saturn=3)
    m = analyse_mangal(ch, lagna_known=True)
    assert m.hits == [("Lagna", 7)]
    assert m.net


def test_mangal_cancelled_by_own_sign():
    # Lagna Taurus, Mars in Scorpio = 7th, but Scorpio is Mars's own sign.
    ch = _chart(Lagna=1, Mars=7, Moon=2, Venus=2, Jupiter=1, Saturn=3)
    m = analyse_mangal(ch, lagna_known=True)
    assert m.raw and not m.net


def test_mangal_house_sign_exception():
    # Lagna Aries, Mars in Cancer = 4th house; exceptions for 4th are Aries/Scorpio only.
    ch = _chart(Lagna=0, Mars=3, Moon=5, Venus=5, Jupiter=1, Saturn=3)
    assert analyse_mangal(ch, True).hits == [("Lagna", 4)]
    # Lagna Gemini, Mars in Taurus = 12th house: a listed exception.
    ch = _chart(Lagna=2, Mars=1, Moon=5, Venus=5, Jupiter=1, Saturn=3)
    m = analyse_mangal(ch, True)
    assert ("Lagna", 12) not in m.hits
    assert m.house_exceptions


# ------------------------------------------------------------------ engine
def test_sun_at_j2000():
    # Apparent tropical longitude of the Sun at 2000-01-01 12:00 UT is ~280.37 deg.
    lon = tropical_longitude(datetime(2000, 1, 1, 12, tzinfo=timezone.utc), "Sun")
    assert lon == pytest.approx(280.37, abs=0.05)


def test_lahiri_ayanamsa_at_j2000():
    ch = calculate_chart(datetime(2000, 1, 1, 12, tzinfo=timezone.utc), 0.0, 0.0)
    assert ch.ayanamsa == pytest.approx(23.85, abs=0.02)


def test_lahiri_applies_in_worker_threads():
    """Streamlit calculates in worker threads; Swiss Ephemeris settings are
    thread-local, so every thread must get the Lahiri ayanamsa."""
    import threading
    when = datetime(1993, 2, 3, 6, 30, tzinfo=timezone.utc)
    main = calculate_chart(when, 19.07, 72.88, False)
    out = {}
    t = threading.Thread(target=lambda: out.setdefault(
        "c", calculate_chart(when, 19.07, 72.88, False)))
    t.start()
    t.join()
    assert out["c"].ayanamsa == pytest.approx(main.ayanamsa, abs=1e-9)
    assert out["c"].longitudes["Moon"] == pytest.approx(main.longitudes["Moon"], abs=1e-9)


def test_ketu_opposite_rahu():
    ch = calculate_chart(datetime(1990, 6, 15, 6, tzinfo=timezone.utc), 12.97, 77.59)
    assert (ch.longitudes["Ketu"] - ch.longitudes["Rahu"]) % 360 == pytest.approx(180)


# ----------------------------------------------------------- time resolution
def test_ist_offset_and_utc():
    rt = resolve_local_time(date(1995, 3, 14), time(6, 45), "Asia/Kolkata")
    assert rt.utc_offset == timedelta(hours=5, minutes=30)
    assert rt.utc == datetime(1995, 3, 14, 1, 15, tzinfo=timezone.utc)


def test_india_war_time():
    rt = resolve_local_time(date(1943, 6, 1), time(10, 0), "Asia/Kolkata")
    assert rt.utc_offset == timedelta(hours=6, minutes=30)


def test_dst_gap_is_flagged():
    # US clocks jumped from 02:00 to 03:00 on 2021-03-14.
    rt = resolve_local_time(date(2021, 3, 14), time(2, 30), "America/New_York")
    assert any(n.key == "tz_gap" for n in rt.notes)


def test_manual_override():
    rt = resolve_local_time(date(1950, 1, 1), time(8, 0), "Asia/Kolkata",
                            override=timedelta(hours=4, minutes=51))
    assert rt.utc == datetime(1950, 1, 1, 3, 9, tzinfo=timezone.utc)
    assert rt.offset_source == "manual"
