from datetime import datetime, timedelta, timezone

import pytest

from kundli import data as D
from kundli.engine import calculate_chart, sweep
from kundli.i18n import NAMES, STRINGS, M, Name, tr
from kundli.matching import Person, match
from kundli.places import resolve_local_time
from kundli.report import build_facts, to_markdown


def test_kannada_has_every_string():
    missing = set(STRINGS["en"]) - set(STRINGS["kn"])
    # Strings that are identical in both languages may fall back to English.
    assert missing <= {"language", "ampm", "place_ph"}


def test_kannada_name_tables_complete():
    for kind, en_table in NAMES["en"].items():
        kn_table = NAMES["kn"][kind]
        keys = range(len(en_table)) if isinstance(en_table, list) else en_table.keys()
        for k in keys:
            assert kn_table[k], (kind, k)


def test_templates_use_same_placeholders():
    import string
    fmt = string.Formatter()
    for key, kn in STRINGS["kn"].items():
        en_fields = {f for _, f, _, _ in fmt.parse(STRINGS["en"][key]) if f}
        kn_fields = {f for _, f, _, _ in fmt.parse(kn) if f}
        assert en_fields == kn_fields, key


def _person(name, when, lat, lon, lagna=True):
    ch = calculate_chart(when, lat, lon, lagna)
    sw = sweep(ch, when - timedelta(hours=12), when + timedelta(hours=12),
               lat, lon, lagna, step_minutes=30)
    return Person(name, ch, sw, lagna)


@pytest.mark.parametrize("lang", ["en", "kn"])
def test_full_report_renders(lang):
    b = _person("B", datetime(1996, 8, 21, 8, 50, tzinfo=timezone.utc), 12.3, 76.6)
    g = _person("G", datetime(1993, 2, 3, 6, 30, tzinfo=timezone.utc), 19.07, 72.88, False)
    r = match(b, g)
    md = to_markdown(b, g, r, {"bride": "x", "groom": "y"}, lang)
    assert "{" not in md and "}" not in md
    if lang == "kn":
        assert "ಅಷ್ಟಕೂಟ" in md and "ವಧು" in md
    facts = build_facts(b, g, r)
    assert facts["total_score"] == r.total


def test_every_possible_koota_value_renders_in_kannada():
    from kundli.engine import MoonPos
    from kundli.matching import (bhakoot_dosha, gana_dosha, nadi_dosha,
                                 score_kootas)
    for nb in range(27):
        for ng in range(0, 27, 4):
            b = MoonPos(nb * 360 / 27 + 1)
            g = MoonPos(ng * 360 / 27 + 7)
            for k in score_kootas(b, g):
                for x in (k.name, k.bride, k.groom, k.note):
                    if x is not None:
                        assert tr(x, "kn")
            for f in (nadi_dosha(b, g), bhakoot_dosha(b, g), gana_dosha(b, g)):
                for x in [f.title, *f.details, *f.parihara]:
                    assert tr(x, "kn")


def test_time_notes_render():
    from datetime import date, time
    rt = resolve_local_time(date(1943, 6, 1), time(10, 0), "Asia/Kolkata")
    assert rt.notes
    for n in rt.notes:
        assert tr(n, "kn") and tr(n, "en")
