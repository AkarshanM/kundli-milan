"""Karnataka conventions: Dashakoota matching, Chandramana calendar, PDFs."""
from datetime import datetime, timedelta, timezone

import pytest

from kundli.dashakoota import (ADHAMA, MADHYAMA, UTTAMA, VEDHA, dashakoota_total,
                               rajju_of, score_dashakoota)
from kundli.engine import MoonPos, calculate_chart, sweep
from kundli.horoscope import build_horoscope, chandramana
from kundli.manual import moon_states_for
from kundli.matching import Person, match
from kundli import kundli_report as KR
from kundli.report import to_markdown

BLR = (12.97, 77.59)


def star(rashi, nak, pada=None):
    return moon_states_for(rashi, nak, pada)[0]


def test_rajju_groups():
    groups = [[n for n in range(27) if rajju_of(n) == r] for r in range(5)]
    assert [len(g) for g in groups] == [6, 6, 6, 6, 3]
    assert groups[4] == [4, 13, 22]               # Shiro: Mrigashira, Chitra, Dhanishta
    assert groups[0] == [0, 8, 9, 17, 18, 26]     # Pada: Ashwini, Ashlesha, Magha, Jyeshtha, Mula, Revati


def test_every_star_has_a_vedha_partner():
    covered = {n for pair in VEDHA for n in pair}
    assert covered == set(range(27))
    assert frozenset((0, 17)) in VEDHA            # Ashwini - Jyeshtha
    assert frozenset((4, 22)) in VEDHA            # Mrigashira - Dhanishta


def by_key(b, g):
    return {k.key: k.result for k in score_dashakoota(b, g)}


def test_test_couple_hand_checked():
    # Bride Vishakha (Tula), groom Mrigashira (Mithuna): 6.5 / 10.
    b, g = star(6, 15, 2), star(2, 4, 3)
    res = by_key(b, g)
    assert res == {"dina": UTTAMA, "gana": ADHAMA, "mahendra": ADHAMA,
                   "stree_deergha": UTTAMA, "yoni": MADHYAMA, "rashi": UTTAMA,
                   "rashyadhipati": UTTAMA, "vashya": ADHAMA, "rajju": UTTAMA,
                   "vedha": UTTAMA}
    assert dashakoota_total(score_dashakoota(b, g)) == 6.5


def test_same_rajju_and_vedha_fail():
    # Ashwini (Mesha) and Jyeshtha (Vrishchika): Vedha pair, both Pada rajju.
    res = by_key(star(0, 0), star(7, 17))
    assert res["vedha"] == ADHAMA and res["rajju"] == ADHAMA


def test_mahendra_and_stree_deergha_counts():
    b = star(0, 0)                          # Ashwini
    assert by_key(b, star(1, 3))["mahendra"] == UTTAMA     # Rohini: count 4
    assert by_key(b, star(4, 9))["stree_deergha"] == MADHYAMA   # Magha: count 10
    assert by_key(b, star(6, 14))["stree_deergha"] == UTTAMA    # Swati: count 15


def test_match_result_has_dashakoota_and_doshas():
    b = Person.from_rashi_nakshatra("B", 0, 0, None, None)
    g = Person.from_rashi_nakshatra("G", 7, 17, None, None)
    r = match(b, g)
    assert r.dk_band == "critical"
    keys = {f.key: f.status for f in r.doshas}
    assert keys["rajju"] == "Present" and keys["vedha"] == "Present"


@pytest.mark.parametrize("when,samvatsara,masa,adhika", [
    (datetime(1996, 8, 21, 8, 50, tzinfo=timezone.utc), "Dhatu", 4, False),
    (datetime(2024, 4, 10, 6, 30, tzinfo=timezone.utc), "Krodhi", 0, False),     # after Ugadi 2024
    (datetime(2024, 4, 5, 6, 30, tzinfo=timezone.utc), "Shobhakrit", 11, False), # before Ugadi
    (datetime(2023, 7, 25, 6, 30, tzinfo=timezone.utc), "Shobhakrit", 4, True),  # Adhika Shravana 2023
    (datetime(2023, 8, 20, 6, 30, tzinfo=timezone.utc), "Shobhakrit", 4, False), # Nija Shravana
])
def test_chandramana_known_dates(when, samvatsara, masa, adhika):
    from kundli.i18n import NAMES
    c = chandramana(calculate_chart(when, *BLR), *BLR)
    assert NAMES["en"]["samvatsara"][c.samvatsara] == samvatsara
    assert c.masa == masa and c.adhika == adhika


def test_ishtakala_and_sunrise():
    c = chandramana(calculate_chart(datetime(1996, 8, 21, 8, 50, tzinfo=timezone.utc), *BLR), *BLR)
    local_rise = c.sunrise + timedelta(hours=5, minutes=30)
    assert (local_rise.hour, local_rise.minute // 10) == (6, 1)   # ~06:1x IST
    assert c.ishtakala[0] == 20                                    # 8h09m = 20.4 ghati


@pytest.mark.parametrize("lang", ["en", "kn"])
def test_pdfs_render(lang):
    from kundli.pdf import render
    when = datetime(1996, 8, 21, 8, 50, tzinfo=timezone.utc)
    ch = calculate_chart(when, *BLR)
    sw = sweep(ch, when - timedelta(minutes=5), when + timedelta(minutes=5), *BLR, True, 1)
    b = Person.from_chart("B", ch, sw, True)
    g = Person.from_rashi_nakshatra("G", 2, 4, None, None)
    r = match(b, g)
    for system in ("karnataka", "north"):
        pdf = render(to_markdown(b, g, r, {}, lang, system=system), "test")
        assert pdf[:4] == b"%PDF" and len(pdf) > 5000
    h = build_horoscope(b, *BLR, utc_offset=timedelta(hours=5, minutes=30))
    charts = [("D1", KR.chart_contents(h, lang), h.lagna_sign),
              ("D9", KR.chart_contents(h, lang, True), h.lagna_navamsa)]
    pdf = render(KR.kundli_markdown(h, lang, "x", for_pdf=True), "test", charts,
                 [str(i) for i in range(12)], "B")
    assert pdf[:4] == b"%PDF"
