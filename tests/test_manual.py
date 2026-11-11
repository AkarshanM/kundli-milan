"""Rashi + nakshatra entry (no birth details)."""
from datetime import datetime, timedelta, timezone

import pytest

from kundli import data as D
from kundli.engine import calculate_chart, sweep
from kundli.i18n import tr
from kundli.manual import moon_states_for, nakshatras_in_rashi, padas_in
from kundli.matching import (CANCELLED, NOT_CHECKED, PRESENT, ABSENT, Person,
                             match, score_kootas, total_score)
from kundli.report import to_markdown


def test_nakshatras_in_each_rashi():
    assert nakshatras_in_rashi(0) == [0, 1, 2]          # Mesha: Ashwini, Bharani, Krittika
    assert nakshatras_in_rashi(1) == [2, 3, 4]          # Vrishabha: Krittika, Rohini, Mrigashira
    assert nakshatras_in_rashi(11) == [24, 25, 26]      # Meena: P.Bhadra, U.Bhadra, Revati
    for r in range(12):
        assert sum(len(padas_in(r, n)) for n in nakshatras_in_rashi(r)) == 9


def test_split_nakshatra_padas():
    assert padas_in(0, 2) == [1]          # Krittika pada 1 in Mesha
    assert padas_in(1, 2) == [2, 3, 4]    # Krittika padas 2-4 in Vrishabha
    assert padas_in(1, 4) == [1, 2]       # Mrigashira padas 1-2 in Vrishabha
    assert padas_in(2, 4) == [3, 4]       # Mrigashira padas 3-4 in Mithuna


@pytest.mark.parametrize("rashi", range(12))
def test_positions_match_entry(rashi):
    for nak in nakshatras_in_rashi(rashi):
        for pada in [None] + padas_in(rashi, nak):
            for m in moon_states_for(rashi, nak, pada):
                assert m.rashi == rashi and m.nakshatra == nak
                if pada:
                    assert m.pada == pada


def test_invalid_combination_rejected():
    with pytest.raises(ValueError):
        moon_states_for(0, 5)    # Ardra is not in Mesha


def test_vashya_half_ambiguity_is_reported():
    # Purva Ashadha pada 1 straddles 15 deg Dhanu: human / quadruped Vashya.
    states = moon_states_for(8, 19, 1)
    assert {m.vashya for m in states} == {D.MANAVA, D.CHATUSHPADA}


def test_same_scores_as_birth_details():
    """Entering the same rashi/nakshatra as a calculated chart gives the
    same Ashtakoota score."""
    when = datetime(1996, 8, 21, 8, 50, tzinfo=timezone.utc)
    ch = calculate_chart(when, 12.3, 76.6)
    m = ch.moon
    manual = moon_states_for(m.rashi, m.nakshatra, m.pada)[0]
    other = moon_states_for(2, 4, 3)[0]       # Mrigashira 3, Mithuna
    assert (total_score(score_kootas(m, other))
            == total_score(score_kootas(manual, other)))


def test_match_both_manual():
    b = Person.from_rashi_nakshatra("B", 6, 15, 2, None)    # Tula, Vishakha 2
    g = Person.from_rashi_nakshatra("G", 2, 4, None, None)  # Mithuna, Mrigashira
    r = match(b, g)
    assert r.total == 20.5
    mangal = [f for f in r.doshas if f.key.startswith("mangal")]
    assert all(f.status == NOT_CHECKED for f in mangal)


def test_declared_manglik_mutual_cancellation():
    b = Person.from_rashi_nakshatra("B", 6, 15, 2, True)
    g = Person.from_rashi_nakshatra("G", 2, 4, None, True)
    statuses = {f.status for f in match(b, g).doshas if f.key.startswith("mangal")}
    assert statuses == {CANCELLED}


def test_declared_manglik_one_side():
    b = Person.from_rashi_nakshatra("B", 6, 15, 2, True)
    g = Person.from_rashi_nakshatra("G", 2, 4, None, False)
    by_key = {f.key: f.status for f in match(b, g).doshas}
    assert by_key["mangal_bride"] == PRESENT
    assert by_key["mangal_groom"] == ABSENT


@pytest.mark.parametrize("lang", ["en", "kn"])
def test_mixed_entry_report(lang):
    when = datetime(1996, 8, 21, 8, 50, tzinfo=timezone.utc)
    ch = calculate_chart(when, 12.3, 76.6)
    sw = sweep(ch, when - timedelta(minutes=5), when + timedelta(minutes=5),
               12.3, 76.6, True, 1)
    b = Person.from_chart("B", ch, sw, True)
    g = Person.from_rashi_nakshatra("G", 2, 4, None, None)
    r = match(b, g)
    md = to_markdown(b, g, r, {"bride": "x", "groom": "y"}, lang)
    assert "{" not in md
    for f in r.doshas:
        assert tr(f.title, lang)
