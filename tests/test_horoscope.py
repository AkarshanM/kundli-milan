"""Individual kundli: checks against independently known values."""
from datetime import datetime, timedelta, timezone

import pytest

from kundli.engine import Chart, calculate_chart, sweep
from kundli.horoscope import (DASHA_YEARS, build_horoscope, dasha_balance,
                              dignity, kaal_sarpa, karana_key, navamsa_sign,
                              panchanga, sade_sati_phase, vimshottari)
from kundli.kundli_report import kundli_facts, kundli_markdown
from kundli.matching import Person

BLR = (12.97, 77.59)   # Bengaluru


def test_navamsa_signs():
    assert navamsa_sign(0.0) == 0      # Mesha 1st navamsa -> Mesha
    assert navamsa_sign(3.4) == 1      # Mesha 2nd -> Vrishabha
    assert navamsa_sign(30.1) == 9     # Vrishabha 1st -> Makara
    assert navamsa_sign(60.1) == 6     # Mithuna 1st -> Tula
    assert navamsa_sign(90.1) == 3     # Karka 1st -> Karka
    assert navamsa_sign(359.9) == 11   # Meena last -> Meena


def test_dignities():
    assert dignity("Sun", 0) == "exalt"
    assert dignity("Sun", 6) == "debil"
    assert dignity("Sun", 4) == "own"
    assert dignity("Mercury", 5) == "exalt"     # Kanya: exalted (and own)
    assert dignity("Saturn", 0) == "debil"
    assert dignity("Rahu", 1) is None


def test_dasha_balance():
    assert dasha_balance(0.0) == ("Ketu", 7, 0, 0)         # start of Ashwini
    assert dasha_balance(20.0) == ("Venus", 10, 0, 0)      # middle of Bharani


def test_dasha_periods_add_up():
    birth = datetime(1990, 1, 1, tzinfo=timezone.utc)
    mds = vimshottari(20.0, birth)
    # Consecutive and the right length
    for a, b in zip(mds, mds[1:]):
        assert a.end == b.start
    for md in mds:
        days = (md.end - md.start).total_seconds() / 86400
        assert days == pytest.approx(DASHA_YEARS[md.lord] * 365.25, abs=1e-6)
        assert md.sub[0].lord == md.lord
        assert md.sub[0].start == md.start and md.sub[-1].end == md.end
    # First MD is Venus and 10 years remain at birth
    assert mds[0].lord == "Venus"
    left = (mds[0].end - birth).total_seconds() / 86400 / 365.25
    assert left == pytest.approx(10.0, abs=1e-6)
    assert [m.lord for m in mds[:3]] == ["Venus", "Sun", "Moon"]


def test_karana():
    assert karana_key(0) == "kimstughna"
    assert karana_key(1) == "bava"
    assert karana_key(7) == "vishti"      # 2nd half of Shukla Chaturthi
    assert karana_key(14) == "vishti"     # 1st half of Shukla Ashtami
    assert karana_key(57) == "shakuni"
    assert karana_key(59) == "naga"


def test_tithi_full_and_new_moon():
    # Full moon 2024-01-25 ~17:54 UT; new moon 2024-04-08 ~18:21 UT.
    ch = calculate_chart(datetime(2024, 1, 25, 12, tzinfo=timezone.utc), *BLR)
    assert panchanga(ch, *BLR).tithi == 14          # Purnima
    ch = calculate_chart(datetime(2024, 4, 8, 12, tzinfo=timezone.utc), *BLR)
    assert panchanga(ch, *BLR).tithi == 29          # Amavasya


def test_vara_changes_at_sunrise():
    # 25 Jan 2024 was a Thursday. 17:30 IST is after sunrise -> Thursday;
    # 05:30 IST is before sunrise (~06:45) -> still Wednesday.
    after = calculate_chart(datetime(2024, 1, 25, 12, 0, tzinfo=timezone.utc), *BLR)
    before = calculate_chart(datetime(2024, 1, 25, 0, 0, tzinfo=timezone.utc), *BLR)
    assert panchanga(after, *BLR).vara == 4      # Thursday (0 = Sunday)
    assert panchanga(before, *BLR).vara == 3     # Wednesday


def test_kaal_sarpa_and_sade_sati():
    lons = {"Rahu": 10.0, "Ketu": 190.0, "Sun": 20, "Moon": 40, "Mars": 60,
            "Mercury": 80, "Jupiter": 100, "Venus": 120, "Saturn": 150}
    ch = Chart(None, 0, lons, 0.0, 0, "test")
    assert kaal_sarpa(ch)
    lons["Saturn"] = 250
    assert not kaal_sarpa(Chart(None, 0, lons, 0.0, 0, "test"))
    assert sade_sati_phase(5, 4) == 1
    assert sade_sati_phase(5, 5) == 2
    assert sade_sati_phase(5, 6) == 3
    assert sade_sati_phase(5, 8) is None


def _horoscope():
    when = datetime(1996, 8, 21, 8, 50, tzinfo=timezone.utc)
    ch = calculate_chart(when, 12.3, 76.6)
    sw = sweep(ch, when - timedelta(minutes=5), when + timedelta(minutes=5),
               12.3, 76.6, True, 1)
    p = Person.from_chart("Test", ch, sw, True)
    return build_horoscope(p, 12.3, 76.6, now=datetime(2026, 11, 11, tzinfo=timezone.utc),
                           utc_offset=timedelta(hours=5, minutes=30))


def test_full_horoscope_builds():
    h = _horoscope()
    assert len(h.planets) == 9
    assert all(1 <= p.house <= 12 for p in h.planets)
    assert h.planets[1].name == "Moon" and h.planets[1].house == (h.planets[1].sign - h.lagna_sign) % 12 + 1
    md, ad = h.current_dasha()
    assert md is not None and ad is not None
    # 21 Aug 1996 was a Wednesday; 14:20 IST is after sunrise.
    assert h.panchanga.vara == 3


@pytest.mark.parametrize("lang", ["en", "kn"])
def test_kundli_report_renders(lang):
    h = _horoscope()
    md = kundli_markdown(h, lang, "resolved")
    assert "{" not in md and "}" not in md
    if lang == "kn":
        assert "ವಿಂಶೋತ್ತರಿ" in md
    facts = kundli_facts(h)
    assert facts["lagna"] and len(facts["planets"]) == 9
