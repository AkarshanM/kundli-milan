"""Translations (English / Kannada).

The engine never builds display sentences itself. It returns `Msg` (a message
key plus parameters) and `Name` (a translatable term such as a nakshatra
index), and `tr(x, lang)` turns them into text at display time. Adding a
language means adding one entry to NAMES and one to STRINGS.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import data as D

LANGUAGES = {"en": "English", "kn": "ಕನ್ನಡ"}


@dataclass(frozen=True, eq=False)
class Msg:
    key: str
    params: dict = field(default_factory=dict)


def M(key: str, **params) -> Msg:
    return Msg(key, params)


@dataclass(frozen=True)
class Name:
    kind: str
    value: object


@dataclass(frozen=True, eq=False)
class Join:
    items: list
    sep: str = ", "


def tr(x, lang: str) -> str:
    if isinstance(x, Msg):
        template = STRINGS.get(lang, {}).get(x.key) or STRINGS["en"][x.key]
        return template.format(**{k: tr(v, lang) for k, v in x.params.items()})
    if isinstance(x, Name):
        table = NAMES.get(lang, {}).get(x.kind) or NAMES["en"][x.kind]
        return table[x.value]
    if isinstance(x, Join):
        return x.sep.join(tr(i, lang) for i in x.items)
    if isinstance(x, float):
        return f"{x:g}"
    return str(x)


_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
            "Rahu", "Ketu", "Lagna"]

NAMES = {
    "en": {
        "nakshatra": D.NAKSHATRAS,
        "rashi": D.RASHIS,
        "planet": {p: p for p in _PLANETS},
        "varna": D.VARNA_NAMES,
        "vashya": D.VASHYA_CLASSES,
        "gana": D.GANA_NAMES,
        "nadi": D.NADI_NAMES,
        "yoni": D.YONI_ANIMALS,
        "sex": {"M": "male", "F": "female"},
        "tara": D.TARA_NAMES,
        "koota": {"varna": "Varna", "vashya": "Vashya", "tara": "Tara",
                  "yoni": "Yoni", "maitri": "Graha Maitri", "gana": "Gana",
                  "bhakoot": "Bhakoot", "nadi": "Nadi"},
        "rel": {"friend": "friend", "neutral": "neutral", "enemy": "enemy",
                "same": "same"},
        "status": {"Absent": "Absent", "Present": "Present",
                   "Mitigated": "Mitigated", "Cancelled": "Cancelled",
                   "NotChecked": "Not checked"},
        "severity": {"none": "none", "mild": "mild", "moderate": "moderate",
                     "strong": "strong"},
        "band": ["Below 18: traditionally not recommended",
                 "18-24: average / acceptable", "25-32: very good",
                 "33-36: excellent"],
        "dignity": {"own": "own sign", "exalt": "exaltation sign"},
        "offset_source": {"tzdb": "timezone database",
                          "manual": "manual override"},
        "quality": {"full": "full marks", "partial": "partial marks",
                    "none": "no marks"},
        "month": ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November",
                  "December"],
    },
    "kn": {
        "nakshatra": [
            "ಅಶ್ವಿನಿ", "ಭರಣಿ", "ಕೃತ್ತಿಕಾ", "ರೋಹಿಣಿ", "ಮೃಗಶಿರಾ", "ಆರ್ದ್ರಾ",
            "ಪುನರ್ವಸು", "ಪುಷ್ಯ", "ಆಶ್ಲೇಷಾ", "ಮಘಾ", "ಪುಬ್ಬ (ಪೂರ್ವ ಫಲ್ಗುಣಿ)",
            "ಉತ್ತರ (ಉತ್ತರ ಫಲ್ಗುಣಿ)", "ಹಸ್ತ", "ಚಿತ್ತಾ", "ಸ್ವಾತಿ", "ವಿಶಾಖಾ",
            "ಅನುರಾಧಾ", "ಜ್ಯೇಷ್ಠಾ", "ಮೂಲಾ", "ಪೂರ್ವಾಷಾಢ", "ಉತ್ತರಾಷಾಢ",
            "ಶ್ರವಣ", "ಧನಿಷ್ಠಾ", "ಶತಭಿಷಾ", "ಪೂರ್ವಾಭಾದ್ರ", "ಉತ್ತರಾಭಾದ್ರ",
            "ರೇವತಿ",
        ],
        "rashi": ["ಮೇಷ", "ವೃಷಭ", "ಮಿಥುನ", "ಕರ್ಕಾಟಕ", "ಸಿಂಹ", "ಕನ್ಯಾ",
                  "ತುಲಾ", "ವೃಶ್ಚಿಕ", "ಧನು", "ಮಕರ", "ಕುಂಭ", "ಮೀನ"],
        "planet": {"Sun": "ಸೂರ್ಯ", "Moon": "ಚಂದ್ರ", "Mars": "ಕುಜ",
                   "Mercury": "ಬುಧ", "Jupiter": "ಗುರು", "Venus": "ಶುಕ್ರ",
                   "Saturn": "ಶನಿ", "Rahu": "ರಾಹು", "Ketu": "ಕೇತು",
                   "Lagna": "ಲಗ್ನ"},
        "varna": {4: "ಬ್ರಾಹ್ಮಣ", 3: "ಕ್ಷತ್ರಿಯ", 2: "ವೈಶ್ಯ", 1: "ಶೂದ್ರ"},
        "vashya": ["ಚತುಷ್ಪಾದ", "ಮಾನವ (ದ್ವಿಪಾದ)", "ಜಲಚರ", "ವನಚರ", "ಕೀಟ"],
        "gana": ["ದೇವ", "ಮನುಷ್ಯ", "ರಾಕ್ಷಸ"],
        "nadi": ["ಆದಿ (ವಾತ)", "ಮಧ್ಯ (ಪಿತ್ತ)", "ಅಂತ್ಯ (ಕಫ)"],
        "yoni": ["ಅಶ್ವ (ಕುದುರೆ)", "ಗಜ (ಆನೆ)", "ಮೇಷ (ಕುರಿ)", "ಸರ್ಪ (ಹಾವು)",
                 "ಶ್ವಾನ (ನಾಯಿ)", "ಮಾರ್ಜಾಲ (ಬೆಕ್ಕು)", "ಮೂಷಕ (ಇಲಿ)",
                 "ಗೋ (ಹಸು)", "ಮಹಿಷ (ಎಮ್ಮೆ)", "ವ್ಯಾಘ್ರ (ಹುಲಿ)",
                 "ಮೃಗ (ಜಿಂಕೆ)", "ವಾನರ (ಕೋತಿ)", "ನಕುಲ (ಮುಂಗುಸಿ)",
                 "ಸಿಂಹ"],
        "sex": {"M": "ಗಂಡು", "F": "ಹೆಣ್ಣು"},
        "tara": {1: "ಜನ್ಮ", 2: "ಸಂಪತ್", 3: "ವಿಪತ್", 4: "ಕ್ಷೇಮ",
                 5: "ಪ್ರತ್ಯಕ್", 6: "ಸಾಧನ", 7: "ನೈಧನ", 8: "ಮಿತ್ರ",
                 0: "ಪರಮ ಮಿತ್ರ"},
        "koota": {"varna": "ವರ್ಣ", "vashya": "ವಶ್ಯ", "tara": "ತಾರಾ",
                  "yoni": "ಯೋನಿ", "maitri": "ಗ್ರಹ ಮೈತ್ರಿ", "gana": "ಗಣ",
                  "bhakoot": "ಭಕೂಟ", "nadi": "ನಾಡಿ"},
        "rel": {"friend": "ಮಿತ್ರ", "neutral": "ಸಮ", "enemy": "ಶತ್ರು",
                "same": "ಒಂದೇ"},
        "status": {"Absent": "ಇಲ್ಲ", "Present": "ಇದೆ",
                   "Mitigated": "ಭಾಗಶಃ ಪರಿಹಾರ",
                   "Cancelled": "ಪರಿಹಾರವಾಗಿದೆ",
                   "NotChecked": "ಪರಿಶೀಲಿಸಿಲ್ಲ"},
        "severity": {"none": "ಇಲ್ಲ", "mild": "ಸೌಮ್ಯ", "moderate": "ಮಧ್ಯಮ",
                     "strong": "ತೀವ್ರ"},
        "band": ["18ಕ್ಕಿಂತ ಕಡಿಮೆ: ಸಾಂಪ್ರದಾಯಿಕವಾಗಿ ಶಿಫಾರಸು ಮಾಡುವುದಿಲ್ಲ",
                 "18-24: ಸಾಧಾರಣ / ಸ್ವೀಕಾರಾರ್ಹ", "25-32: ಉತ್ತಮ",
                 "33-36: ಅತ್ಯುತ್ತಮ"],
        "dignity": {"own": "ಸ್ವಕ್ಷೇತ್ರ", "exalt": "ಉಚ್ಚ ಸ್ಥಾನ"},
        "offset_source": {"tzdb": "ಸಮಯ ವಲಯ ದತ್ತಾಂಶ",
                          "manual": "ಕೈಯಾರೆ ನಮೂದಿಸಿದ್ದು"},
        "quality": {"full": "ಪೂರ್ಣ ಅಂಕ", "partial": "ಭಾಗಶಃ ಅಂಕ",
                    "none": "ಅಂಕ ಇಲ್ಲ"},
        "month": ["ಜನವರಿ", "ಫೆಬ್ರವರಿ", "ಮಾರ್ಚ್", "ಏಪ್ರಿಲ್", "ಮೇ", "ಜೂನ್",
                  "ಜುಲೈ", "ಆಗಸ್ಟ್", "ಸೆಪ್ಟೆಂಬರ್", "ಅಕ್ಟೋಬರ್", "ನವೆಂಬರ್",
                  "ಡಿಸೆಂಬರ್"],
    },
}

STRINGS = {
    "en": {
        # ---- engine: koota values and notes
        "moon_state": "{nak} pada {pada}, {rashi}",
        "tara_value_bride": "{tara} (groom's star is #{n} from hers)",
        "tara_value_groom": "{tara} (bride's star is #{n} from his)",
        "tara_note": "Vipat, Pratyak and Naidhana are the unfavourable taras.",
        "yoni_value": "{animal} ({sex})",
        "maitri_value": "{lord} (lord of {rashi})",
        "maitri_note": "{a} → {b}: {rel_ab}; {b} → {a}: {rel_ba}.",
        "bhakoot_note": "Moon signs are in a {label} relationship.",
        # ---- engine: doshas
        "dosha_nadi": "Nadi Dosha",
        "dosha_bhakoot": "Bhakoot Dosha",
        "dosha_gana": "Gana Dosha",
        "dosha_mangal": "Mangal Dosha: {name}",
        "nadi_different": "Different Nadis ({b} / {g}).",
        "nadi_same": "Both partners have {nadi} Nadi (Nadi koota 0/8).",
        "nadi_ph_same_rashi": "Same Moon sign but different nakshatras.",
        "nadi_ph_same_nak": "Same nakshatra but the Moons are in different signs.",
        "nadi_ph_diff_pada": "Same nakshatra and sign but different padas "
                             "(accepted as a relief by some traditions).",
        "nadi_same_pada": "Same nakshatra and same pada: traditionally the "
                          "strongest form, with no standard cancellation.",
        "nadi_ph_lords_friends": "Moon-sign lords {a} and {b} are mutual "
                                 "friends (accepted as a relief by some traditions).",
        "bhakoot_ok": "Moon signs are {label} from each other, which is favourable.",
        "bhakoot_bad": "Moon signs are {label} from each other (Bhakoot koota 0/7).",
        "bhakoot_59_mild": "Some traditions treat 5/9 as milder than 6/8 or 2/12.",
        "bhakoot_ph_same_lord": "Both Moon signs are ruled by {lord}.",
        "bhakoot_ph_friends": "Moon-sign lords {a} and {b} are mutual friends.",
        "bhakoot_ph_half": "Moon-sign lords {a} and {b} are friendly on one "
                           "side and neutral on the other.",
        "gana_ok": "Ganas {b} / {g} are compatible.",
        "gana_bad": "Ganas {b} (bride) and {g} (groom) are a difficult pair "
                    "(Gana koota {pts}/6).",
        "gana_ph_lords": "The Moon-sign lords are the same or mutual friends.",
        "gana_ph_lords_half": "The Moon-sign lords are friendly.",
        "gana_ph_bhakoot": "Bhakoot is favourable.",
        "mangal_checked": "Checked from: {refs}.",
        "mangal_no_lagna": "Birth time unknown, so the Lagna was not used.",
        "mangal_exception": "From {ref}: Mars in house {house} in {sign} is a "
                            "traditional exception.",
        "mangal_absent": "Mars is not in houses 1, 2, 4, 7, 8 or 12 from any "
                         "reference point (after exceptions).",
        "mangal_hit": "house {house} from {ref}",
        "mangal_hits": "Mars in {hits} (intensity: {sev}).",
        "mangal_ph_own": "Mars is in {sign}, its {kind}.",
        "mangal_ph_jup_conj": "Mars is conjunct Jupiter.",
        "mangal_ph_jup_aspect": "Mars receives Jupiter's aspect (house {rel} "
                                "from Jupiter).",
        "mangal_ph_moon_conj": "Mars is conjunct the Moon (Chandra-Mangala yoga).",
        "mangal_ph_mutual": "Both partners have Mangal Dosha: mutual "
                            "cancellation (the most widely applied rule).",
        "mangal_ph_saturn": "Partner has Saturn in house {house} from {ref} "
                            "(dosha samya / balancing).",
        "mangal_time_sensitive": "Within the birth-time window this result "
                                 "changes (the Lagna or Moon moves into a "
                                 "different sign), so it depends on the exact "
                                 "birth time.",
        "couple_time_sensitive": "This result can change with details that "
                                 "weren't given exactly (birth time or pada).",
        "moon_state_no_pada": "{nak} (pada not given), {rashi}",
        "mangal_not_checked": "Not checked: this needs birth date, time and "
                              "place, or tell the app whether this person "
                              "is Manglik.",
        "mangal_declared_yes": "Marked as Manglik in the details entered "
                               "(not calculated here).",
        "mangal_declared_no": "Marked as not Manglik in the details entered "
                              "(not calculated here).",
        "note_manual_uncertain": "{name}: Vashya depends on the exact Moon "
                                 "degree, which wasn't given. It could be "
                                 "{states}.",
        # ---- rashi / nakshatra entry
        "mode_label": "How do you want to enter the details?",
        "mode_birth": "Birth date, time and place (most accurate)",
        "mode_star": "Rashi and nakshatra (if already known)",
        "rashi_q": "Rashi (Moon sign)",
        "nak_q": "Nakshatra (birth star)",
        "pada_q": "Pada",
        "pada_unknown": "Don't know",
        "pada_value": "Pada {p}",
        "manglik_q": "Mangal (Kuja) Dosha, if known from the horoscope",
        "manglik_unknown": "Don't know",
        "manglik_yes": "Yes, Manglik",
        "manglik_no": "No",
        "star_info": "Rashi and nakshatra are enough for the 36-point "
                     "Ashtakoota score. Mangal Dosha needs the position of "
                     "Mars, so it uses the answer above (or is skipped).",
        "need_rashi": "rashi",
        "need_nak": "nakshatra",
        "entered_text": "Entered directly: {rashi}, {nak}, {pada}",
        "pada_not_given": "pada not given",
        "chart_entered": "Entered as rashi and nakshatra, so planetary "
                         "positions aren't available.",
        "note_moon_boundary": "{name}'s Moon is near a boundary. Within the "
                              "birth-time window it could be: {states}.",
        "note_lagna_changes": "{name}'s Lagna (ascendant) changes within the "
                              "birth-time window: {signs}.",
        # ---- place / time notes
        "tz_gap": "This clock time was skipped when clocks moved forward "
                  "(daylight saving). Using {off}; override the offset if you "
                  "know better.",
        "tz_fold": "This clock time happened twice when clocks moved back "
                   "(daylight saving). Using the first, {off}; the second "
                   "would be {off2}. Override the offset if needed.",
        "tz_pre1970": "Timezone records before 1970 are less reliable. Please "
                      "double-check the UTC offset shown.",
        "tz_india_local": "Before 1948 (Kolkata) and 1955 (Mumbai) those "
                          "cities also kept local times: Calcutta Time "
                          "UTC+05:53:20, Bombay Time UTC+04:51. If the birth "
                          "was there and recorded in local time, set the "
                          "offset manually.",
        "tz_war_time": "India used war time (UTC+06:30) in parts of "
                       "1941-1945. The database applies it here; confirm with "
                       "family records if possible.",
        # ---- koota meanings
        "meaning_varna": "Spiritual and work temperament (ego compatibility). "
                         "Traditionally the groom's varna should be equal to "
                         "or higher than the bride's. Here it describes "
                         "temperament, not caste.",
        "meaning_vashya": "Mutual attraction and the balance of influence in "
                          "the relationship.",
        "meaning_tara": "Birth-star (destiny) compatibility, counted from each "
                        "partner's nakshatra to the other's.",
        "meaning_yoni": "Physical and instinctive compatibility, from the "
                        "animal symbol of each nakshatra.",
        "meaning_maitri": "Mental wavelength and friendship, from the natural "
                          "friendship between the two Moon-sign lords.",
        "meaning_gana": "Temperament: Deva (gentle), Manushya (balanced), "
                        "Rakshasa (intense).",
        "meaning_bhakoot": "How the two Moon signs sit relative to each other. "
                           "Traditionally linked with family welfare, finances "
                           "and emotional harmony.",
        "meaning_nadi": "The most heavily weighted koota, traditionally linked "
                        "with health and progeny. It is a traditional "
                        "indicator, not a medical or genetic test.",
        # ---- UI
        "title": "Kundli Milan",
        "caption": "Ashtakoota (36 Guna) matching · Swiss Ephemeris · Lahiri ayanamsa",
        "language": "Language / ಭಾಷೆ",
        "password": "Password",
        "wrong_password": "Wrong password.",
        "bride": "Bride",
        "groom": "Groom",
        "full_name": "Full name",
        "dob": "Date of birth",
        "day": "Day",
        "month": "Month",
        "year": "Year",
        "invalid_date": "{month} {year} has no day {day}.",
        "accuracy_q": "How accurate is the birth time?",
        "acc_exact": "Exact (birth certificate / hospital record)",
        "acc_approx_15m": "Approximate (within about 15 minutes)",
        "acc_approx_1h": "Rough (within about an hour)",
        "acc_unknown": "Unknown",
        "hour": "Hour",
        "minute": "Minute",
        "ampm": "AM / PM",
        "AM": "AM",
        "PM": "PM",
        "time24": "24-hour time: **{t}**{hint}",
        "hint_midnight": " (just after midnight)",
        "hint_noon": " (noon)",
        "manual_coords": "Enter coordinates manually instead of searching",
        "lat": "Latitude (north +)",
        "lon": "Longitude (east +)",
        "timezone": "Timezone",
        "place_q": "Place of birth (city or town name only)",
        "place_ph": "e.g. Mysuru",
        "place_fail": "Place lookup failed. Check the internet connection, or "
                      "tick 'Enter coordinates manually'.",
        "choose_place": "Choose the exact place",
        "no_match": "No match. Try another spelling (e.g. Bengaluru / "
                    "Bangalore) or enter coordinates manually.",
        "override": "Override UTC offset (only if the timezone shown below is wrong)",
        "sign": "Sign",
        "hours": "Hours",
        "minutes": "Minutes",
        "still_needed": "Still needed: {items}",
        "need_name": "name",
        "need_dob": "date of birth",
        "need_time": "time of birth (hour, minute and AM/PM)",
        "need_place": "place of birth",
        "please_check": "**Please check:** {text}",
        "when_known": "{date}, {time} local",
        "when_unknown": "{date}, time unknown (noon used for the Moon)",
        "unknown_info": "Birth time unknown: the Lagna can't be used, and the "
                        "Moon is checked across the whole day.",
        "calc_button": "Details are correct: calculate match",
        "calculating": "Calculating charts...",
        "details_changed": "The details have changed. Click **calculate "
                           "match** again to update the results.",
        "score_metric": "Guna Milan score",
        "band_label": "Band",
        "range_label": "Possible range (birth time / pada not exact)",
        "range_value": "{a} to {b}",
        "ashtakoota": "Ashtakoota",
        "col_koota": "Koota",
        "col_score": "Score",
        "what_means": "What each koota means",
        "doshas_header": "Doshas and cancellations",
        "doshas_caption": "A cancellation (parihara) doesn't change the "
                          "36-point score; it changes whether the dosha is "
                          "traditionally a concern.",
        "depends_time": "⏱️ *depends on exact birth time / pada*",
        "parihara_applied": "*Parihara (cancellation) applied:*",
        "sensitivity_header": "Sensitivity to birth time / pada",
        "chart_details": "Chart details",
        "chart_of": "{name}'s chart",
        "moon_label": "**Moon:** {state}",
        "col_body": "Body",
        "col_sign": "Sign",
        "col_degree": "Degree",
        "col_nak": "Nakshatra (pada)",
        "chart_caption": "Lahiri ayanamsa {aya} · {eph} · whole-sign houses",
        "ai_header": "Interpretation (AI)",
        "ai_language": "Language",
        "ai_button": "Write interpretation",
        "ai_spinner": "Writing the interpretation (about 30 seconds)...",
        "ai_caption": "Written by AI from the calculated values above. The "
                      "table and dosha results are the source of truth.",
        "download": "Download report (Markdown)",
        "footer": "For personal use. Calculations follow common North Indian "
                  "Ashtakoota conventions; regional traditions differ. "
                  "Astrology is one input among many: values, respect and "
                  "communication matter most.",
        # ---- Markdown report
        "md_title": "Kundli Milan: {b} & {g}",
        "md_total": "**Total: {total} / 36** ({band})",
        "md_range": "Score range within the birth-time window: {a}-{b}",
        "md_birth_data": "Birth data used",
        "md_moon_line": "Moon: {moon}; Lagna: {lagna}",
        "lagna_unknown": "unknown (birth time unknown)",
        "md_doshas": "Doshas",
        "md_parihara": "Parihara: {p}",
        "md_interpretation": "Interpretation",
        "md_footer": "Calculated with Swiss Ephemeris (Lahiri ayanamsa). "
                     "Astrology is one input among many: values, respect and "
                     "communication matter most.",
    },
    "kn": {
        "moon_state": "{nak} {pada}ನೇ ಪಾದ, {rashi}",
        "tara_value_bride": "{tara} (ವಧುವಿನ ನಕ್ಷತ್ರದಿಂದ ವರನದು {n}ನೇ)",
        "tara_value_groom": "{tara} (ವರನ ನಕ್ಷತ್ರದಿಂದ ವಧುವಿನದು {n}ನೇ)",
        "tara_note": "ವಿಪತ್, ಪ್ರತ್ಯಕ್ ಮತ್ತು ನೈಧನ ತಾರೆಗಳು ಅಶುಭ.",
        "yoni_value": "{animal} ({sex})",
        "maitri_value": "{lord} ({rashi} ರಾಶ್ಯಧಿಪತಿ)",
        "maitri_note": "{a} → {b}: {rel_ab}; {b} → {a}: {rel_ba}.",
        "bhakoot_note": "ಚಂದ್ರ ರಾಶಿಗಳು ಪರಸ್ಪರ {label} ಸ್ಥಾನದಲ್ಲಿವೆ.",
        "dosha_nadi": "ನಾಡಿ ದೋಷ",
        "dosha_bhakoot": "ಭಕೂಟ ದೋಷ",
        "dosha_gana": "ಗಣ ದೋಷ",
        "dosha_mangal": "ಕುಜ ದೋಷ: {name}",
        "nadi_different": "ನಾಡಿಗಳು ಬೇರೆ ಬೇರೆ ({b} / {g}).",
        "nadi_same": "ಇಬ್ಬರಿಗೂ {nadi} ನಾಡಿ (ನಾಡಿ ಕೂಟ 0/8).",
        "nadi_ph_same_rashi": "ಚಂದ್ರ ರಾಶಿ ಒಂದೇ, ಆದರೆ ನಕ್ಷತ್ರಗಳು ಬೇರೆ.",
        "nadi_ph_same_nak": "ನಕ್ಷತ್ರ ಒಂದೇ, ಆದರೆ ಚಂದ್ರ ರಾಶಿಗಳು ಬೇರೆ.",
        "nadi_ph_diff_pada": "ನಕ್ಷತ್ರ ಮತ್ತು ರಾಶಿ ಒಂದೇ, ಆದರೆ ಪಾದಗಳು ಬೇರೆ "
                             "(ಕೆಲವು ಸಂಪ್ರದಾಯಗಳಲ್ಲಿ ಪರಿಹಾರವೆಂದು ಪರಿಗಣಿಸಲಾಗುತ್ತದೆ).",
        "nadi_same_pada": "ನಕ್ಷತ್ರ ಮತ್ತು ಪಾದ ಎರಡೂ ಒಂದೇ: ಸಾಂಪ್ರದಾಯಿಕವಾಗಿ ಇದು "
                          "ಅತ್ಯಂತ ಪ್ರಬಲ ರೂಪ; ಸಾಮಾನ್ಯ ಪರಿಹಾರ ಅನ್ವಯಿಸುವುದಿಲ್ಲ.",
        "nadi_ph_lords_friends": "ರಾಶ್ಯಧಿಪತಿಗಳಾದ {a} ಮತ್ತು {b} ಪರಸ್ಪರ ಮಿತ್ರರು "
                                 "(ಕೆಲವು ಸಂಪ್ರದಾಯಗಳಲ್ಲಿ ಪರಿಹಾರವೆಂದು ಪರಿಗಣಿಸಲಾಗುತ್ತದೆ).",
        "bhakoot_ok": "ಚಂದ್ರ ರಾಶಿಗಳು ಪರಸ್ಪರ {label} ಸ್ಥಾನದಲ್ಲಿವೆ; ಇದು ಶುಭ.",
        "bhakoot_bad": "ಚಂದ್ರ ರಾಶಿಗಳು ಪರಸ್ಪರ {label} ಸ್ಥಾನದಲ್ಲಿವೆ (ಭಕೂಟ 0/7).",
        "bhakoot_59_mild": "ಕೆಲವು ಸಂಪ್ರದಾಯಗಳಲ್ಲಿ 5/9 ಅನ್ನು 6/8 ಅಥವಾ 2/12 ಗಿಂತ "
                           "ಸೌಮ್ಯವೆಂದು ಪರಿಗಣಿಸಲಾಗುತ್ತದೆ.",
        "bhakoot_ph_same_lord": "ಎರಡೂ ಚಂದ್ರ ರಾಶಿಗಳ ಅಧಿಪತಿ {lord}.",
        "bhakoot_ph_friends": "ರಾಶ್ಯಧಿಪತಿಗಳಾದ {a} ಮತ್ತು {b} ಪರಸ್ಪರ ಮಿತ್ರರು.",
        "bhakoot_ph_half": "ರಾಶ್ಯಧಿಪತಿಗಳಾದ {a} ಮತ್ತು {b} ಒಂದು ಕಡೆ ಮಿತ್ರ, "
                           "ಇನ್ನೊಂದು ಕಡೆ ಸಮ.",
        "gana_ok": "ಗಣಗಳು {b} / {g} ಹೊಂದಿಕೆಯಾಗುತ್ತವೆ.",
        "gana_bad": "ವಧುವಿನ {b} ಗಣ ಮತ್ತು ವರನ {g} ಗಣ ಕಷ್ಟಕರ ಜೋಡಿ "
                    "(ಗಣ ಕೂಟ {pts}/6).",
        "gana_ph_lords": "ರಾಶ್ಯಧಿಪತಿಗಳು ಒಂದೇ ಅಥವಾ ಪರಸ್ಪರ ಮಿತ್ರರು.",
        "gana_ph_lords_half": "ರಾಶ್ಯಧಿಪತಿಗಳು ಸ್ನೇಹಪರರು.",
        "gana_ph_bhakoot": "ಭಕೂಟ ಶುಭವಾಗಿದೆ.",
        "mangal_checked": "ಪರಿಶೀಲಿಸಿದ ಆಧಾರಗಳು: {refs}.",
        "mangal_no_lagna": "ಜನ್ಮ ಸಮಯ ತಿಳಿದಿಲ್ಲ, ಆದ್ದರಿಂದ ಲಗ್ನವನ್ನು ಬಳಸಲಾಗಿಲ್ಲ.",
        "mangal_exception": "{ref} ಆಧಾರದಲ್ಲಿ: {sign} ರಾಶಿಯಲ್ಲಿ {house}ನೇ "
                            "ಮನೆಯ ಕುಜ ಸಾಂಪ್ರದಾಯಿಕ ವಿನಾಯಿತಿ.",
        "mangal_absent": "ಯಾವುದೇ ಆಧಾರದಿಂದಲೂ ಕುಜ 1, 2, 4, 7, 8 ಅಥವಾ 12ನೇ "
                         "ಮನೆಯಲ್ಲಿಲ್ಲ (ವಿನಾಯಿತಿಗಳ ನಂತರ).",
        "mangal_hit": "{ref} ಆಧಾರದಲ್ಲಿ {house}ನೇ ಮನೆ",
        "mangal_hits": "ಕುಜ: {hits} (ತೀವ್ರತೆ: {sev}).",
        "mangal_ph_own": "ಕುಜ {sign} ರಾಶಿಯಲ್ಲಿದೆ, ಅದು ಕುಜನ {kind}.",
        "mangal_ph_jup_conj": "ಕುಜ ಗುರುವಿನೊಂದಿಗೆ ಯುತಿಯಲ್ಲಿದೆ.",
        "mangal_ph_jup_aspect": "ಕುಜನಿಗೆ ಗುರು ದೃಷ್ಟಿ ಇದೆ (ಗುರುವಿನಿಂದ {rel}ನೇ ಮನೆ).",
        "mangal_ph_moon_conj": "ಕುಜ ಚಂದ್ರನೊಂದಿಗೆ ಯುತಿಯಲ್ಲಿದೆ (ಚಂದ್ರ-ಮಂಗಳ ಯೋಗ).",
        "mangal_ph_mutual": "ಇಬ್ಬರಿಗೂ ಕುಜ ದೋಷ ಇದೆ: ಪರಸ್ಪರ ಪರಿಹಾರ "
                            "(ಅತ್ಯಂತ ವ್ಯಾಪಕವಾಗಿ ಅನ್ವಯಿಸುವ ನಿಯಮ).",
        "mangal_ph_saturn": "ಸಂಗಾತಿಯ ಜಾತಕದಲ್ಲಿ {ref} ಆಧಾರದಲ್ಲಿ {house}ನೇ "
                            "ಮನೆಯಲ್ಲಿ ಶನಿ ಇದೆ (ದೋಷ ಸಾಮ್ಯ).",
        "mangal_time_sensitive": "ಜನ್ಮ ಸಮಯದ ಅಂತರದೊಳಗೆ ಈ ಫಲಿತಾಂಶ ಬದಲಾಗುತ್ತದೆ "
                                 "(ಲಗ್ನ ಅಥವಾ ಚಂದ್ರ ಬೇರೆ ರಾಶಿಗೆ ಹೋಗುತ್ತದೆ), "
                                 "ಆದ್ದರಿಂದ ಇದು ನಿಖರ ಜನ್ಮ ಸಮಯವನ್ನು ಅವಲಂಬಿಸಿದೆ.",
        "couple_time_sensitive": "ನಿಖರವಾಗಿ ನೀಡದ ವಿವರಗಳಿಂದ (ಜನ್ಮ ಸಮಯ ಅಥವಾ "
                                 "ಪಾದ) ಈ ಫಲಿತಾಂಶ ಬದಲಾಗಬಹುದು.",
        "moon_state_no_pada": "{nak} (ಪಾದ ನೀಡಿಲ್ಲ), {rashi}",
        "mangal_not_checked": "ಪರಿಶೀಲಿಸಿಲ್ಲ: ಇದಕ್ಕೆ ಜನ್ಮ ದಿನಾಂಕ, ಸಮಯ ಮತ್ತು "
                              "ಸ್ಥಳ ಬೇಕು, ಅಥವಾ ಈ ವ್ಯಕ್ತಿಗೆ ಕುಜ ದೋಷ ಇದೆಯೇ "
                              "ಎಂದು ತಿಳಿಸಿ.",
        "mangal_declared_yes": "ನಮೂದಿಸಿದ ವಿವರಗಳಲ್ಲಿ ಕುಜ ದೋಷ ಇದೆ ಎಂದು "
                               "ಗುರುತಿಸಲಾಗಿದೆ (ಇಲ್ಲಿ ಲೆಕ್ಕಹಾಕಿಲ್ಲ).",
        "mangal_declared_no": "ನಮೂದಿಸಿದ ವಿವರಗಳಲ್ಲಿ ಕುಜ ದೋಷ ಇಲ್ಲ ಎಂದು "
                              "ಗುರುತಿಸಲಾಗಿದೆ (ಇಲ್ಲಿ ಲೆಕ್ಕಹಾಕಿಲ್ಲ).",
        "note_manual_uncertain": "{name}: ವಶ್ಯವು ಚಂದ್ರನ ನಿಖರ ಅಂಶವನ್ನು "
                                 "ಅವಲಂಬಿಸಿದೆ, ಅದನ್ನು ನೀಡಿಲ್ಲ. ಅದು {states} "
                                 "ಆಗಿರಬಹುದು.",
        "mode_label": "ವಿವರಗಳನ್ನು ಹೇಗೆ ನಮೂದಿಸಲು ಬಯಸುತ್ತೀರಿ?",
        "mode_birth": "ಜನ್ಮ ದಿನಾಂಕ, ಸಮಯ ಮತ್ತು ಸ್ಥಳ (ಅತ್ಯಂತ ನಿಖರ)",
        "mode_star": "ರಾಶಿ ಮತ್ತು ನಕ್ಷತ್ರ (ಈಗಾಗಲೇ ತಿಳಿದಿದ್ದರೆ)",
        "rashi_q": "ರಾಶಿ (ಚಂದ್ರ ರಾಶಿ)",
        "nak_q": "ನಕ್ಷತ್ರ (ಜನ್ಮ ನಕ್ಷತ್ರ)",
        "pada_q": "ಪಾದ",
        "pada_unknown": "ಗೊತ್ತಿಲ್ಲ",
        "pada_value": "{p}ನೇ ಪಾದ",
        "manglik_q": "ಕುಜ ದೋಷ (ಜಾತಕದಲ್ಲಿ ತಿಳಿದಿದ್ದರೆ)",
        "manglik_unknown": "ಗೊತ್ತಿಲ್ಲ",
        "manglik_yes": "ಹೌದು, ಕುಜ ದೋಷ ಇದೆ",
        "manglik_no": "ಇಲ್ಲ",
        "star_info": "36 ಅಂಕಗಳ ಅಷ್ಟಕೂಟಕ್ಕೆ ರಾಶಿ ಮತ್ತು ನಕ್ಷತ್ರ ಸಾಕು. ಕುಜ "
                     "ದೋಷಕ್ಕೆ ಕುಜನ ಸ್ಥಾನ ಬೇಕು, ಆದ್ದರಿಂದ ಮೇಲಿನ ಉತ್ತರವನ್ನು "
                     "ಬಳಸಲಾಗುತ್ತದೆ (ಅಥವಾ ಬಿಡಲಾಗುತ್ತದೆ).",
        "need_rashi": "ರಾಶಿ",
        "need_nak": "ನಕ್ಷತ್ರ",
        "entered_text": "ನೇರವಾಗಿ ನಮೂದಿಸಲಾಗಿದೆ: {rashi}, {nak}, {pada}",
        "pada_not_given": "ಪಾದ ನೀಡಿಲ್ಲ",
        "chart_entered": "ರಾಶಿ ಮತ್ತು ನಕ್ಷತ್ರವಾಗಿ ನಮೂದಿಸಲಾಗಿದೆ, ಆದ್ದರಿಂದ ಗ್ರಹ "
                         "ಸ್ಥಾನಗಳು ಲಭ್ಯವಿಲ್ಲ.",
        "note_moon_boundary": "{name} ಅವರ ಚಂದ್ರ ಗಡಿಯ ಹತ್ತಿರವಿದೆ. ಜನ್ಮ ಸಮಯದ "
                              "ಅಂತರದೊಳಗೆ ಅದು ಹೀಗಿರಬಹುದು: {states}.",
        "note_lagna_changes": "{name} ಅವರ ಲಗ್ನ ಜನ್ಮ ಸಮಯದ ಅಂತರದೊಳಗೆ "
                              "ಬದಲಾಗುತ್ತದೆ: {signs}.",
        "tz_gap": "ಗಡಿಯಾರಗಳನ್ನು ಮುಂದೆ ಸರಿಸಿದಾಗ (ಡೇಲೈಟ್ ಸೇವಿಂಗ್) ಈ ಸಮಯ "
                  "ಇರಲಿಲ್ಲ. {off} ಬಳಸಲಾಗುತ್ತಿದೆ; ಸರಿಯಾದ ಮಾಹಿತಿ ಇದ್ದರೆ "
                  "ಆಫ್‌ಸೆಟ್ ಬದಲಿಸಿ.",
        "tz_fold": "ಗಡಿಯಾರಗಳನ್ನು ಹಿಂದೆ ಸರಿಸಿದಾಗ (ಡೇಲೈಟ್ ಸೇವಿಂಗ್) ಈ ಸಮಯ "
                   "ಎರಡು ಬಾರಿ ಬಂದಿತ್ತು. ಮೊದಲನೆಯದು, {off}, ಬಳಸಲಾಗುತ್ತಿದೆ; "
                   "ಎರಡನೆಯದು {off2}. ಅಗತ್ಯವಿದ್ದರೆ ಆಫ್‌ಸೆಟ್ ಬದಲಿಸಿ.",
        "tz_pre1970": "1970ಕ್ಕಿಂತ ಹಿಂದಿನ ಸಮಯ ವಲಯ ದಾಖಲೆಗಳು ಕಡಿಮೆ ವಿಶ್ವಾಸಾರ್ಹ. "
                      "ತೋರಿಸಿರುವ UTC ಆಫ್‌ಸೆಟ್ ಅನ್ನು ಮತ್ತೊಮ್ಮೆ ಪರಿಶೀಲಿಸಿ.",
        "tz_india_local": "1948 (ಕೋಲ್ಕತ್ತಾ) ಮತ್ತು 1955 (ಮುಂಬೈ) ಕ್ಕಿಂತ ಮೊದಲು ಆ "
                          "ನಗರಗಳು ಸ್ಥಳೀಯ ಸಮಯವನ್ನೂ ಬಳಸುತ್ತಿದ್ದವು: ಕಲ್ಕತ್ತಾ "
                          "ಸಮಯ UTC+05:53:20, ಬಾಂಬೆ ಸಮಯ UTC+04:51. ಜನನ ಅಲ್ಲಿ "
                          "ಆಗಿದ್ದು ಸ್ಥಳೀಯ ಸಮಯದಲ್ಲಿ ದಾಖಲಾಗಿದ್ದರೆ, ಆಫ್‌ಸೆಟ್ ಅನ್ನು "
                          "ಕೈಯಾರೆ ನಮೂದಿಸಿ.",
        "tz_war_time": "1941-1945ರ ಕೆಲವು ಅವಧಿಗಳಲ್ಲಿ ಭಾರತ ಯುದ್ಧಕಾಲದ ಸಮಯ "
                       "(UTC+06:30) ಬಳಸಿತು. ಇಲ್ಲಿ ಅದನ್ನು ಅನ್ವಯಿಸಲಾಗಿದೆ; "
                       "ಸಾಧ್ಯವಾದರೆ ಕುಟುಂಬದ ದಾಖಲೆಗಳೊಂದಿಗೆ ಖಚಿತಪಡಿಸಿ.",
        "meaning_varna": "ಆಧ್ಯಾತ್ಮಿಕ ಮತ್ತು ಕೆಲಸದ ಸ್ವಭಾವ (ಅಹಂ ಹೊಂದಾಣಿಕೆ). "
                         "ಸಾಂಪ್ರದಾಯಿಕವಾಗಿ ವರನ ವರ್ಣ ವಧುವಿನದಕ್ಕೆ ಸಮ ಅಥವಾ "
                         "ಹೆಚ್ಚು ಇರಬೇಕು. ಇಲ್ಲಿ ಇದು ಸ್ವಭಾವವನ್ನು ಸೂಚಿಸುತ್ತದೆ, "
                         "ಜಾತಿಯನ್ನಲ್ಲ.",
        "meaning_vashya": "ಪರಸ್ಪರ ಆಕರ್ಷಣೆ ಮತ್ತು ಸಂಬಂಧದಲ್ಲಿ ಪ್ರಭಾವದ ಸಮತೋಲನ.",
        "meaning_tara": "ಜನ್ಮ ನಕ್ಷತ್ರದ (ಭಾಗ್ಯ) ಹೊಂದಾಣಿಕೆ; ಒಬ್ಬರ ನಕ್ಷತ್ರದಿಂದ "
                        "ಇನ್ನೊಬ್ಬರ ನಕ್ಷತ್ರಕ್ಕೆ ಎಣಿಸಲಾಗುತ್ತದೆ.",
        "meaning_yoni": "ದೈಹಿಕ ಮತ್ತು ಸಹಜ ಸ್ವಭಾವದ ಹೊಂದಾಣಿಕೆ; ಪ್ರತಿ ನಕ್ಷತ್ರದ "
                        "ಪ್ರಾಣಿ ಚಿಹ್ನೆಯಿಂದ.",
        "meaning_maitri": "ಮಾನಸಿಕ ಹೊಂದಾಣಿಕೆ ಮತ್ತು ಸ್ನೇಹ; ಎರಡು ಚಂದ್ರ ರಾಶಿಗಳ "
                          "ಅಧಿಪತಿಗಳ ನೈಸರ್ಗಿಕ ಮೈತ್ರಿಯಿಂದ.",
        "meaning_gana": "ಸ್ವಭಾವ: ದೇವ (ಸೌಮ್ಯ), ಮನುಷ್ಯ (ಸಮತೋಲನ), ರಾಕ್ಷಸ (ತೀವ್ರ).",
        "meaning_bhakoot": "ಎರಡು ಚಂದ್ರ ರಾಶಿಗಳ ಪರಸ್ಪರ ಸ್ಥಾನ. ಸಾಂಪ್ರದಾಯಿಕವಾಗಿ "
                           "ಕುಟುಂಬ ಕ್ಷೇಮ, ಆರ್ಥಿಕ ಸ್ಥಿತಿ ಮತ್ತು ಭಾವನಾತ್ಮಕ "
                           "ಸಾಮರಸ್ಯಕ್ಕೆ ಸಂಬಂಧಿಸಿದೆ.",
        "meaning_nadi": "ಅತಿ ಹೆಚ್ಚು ಅಂಕಗಳ ಕೂಟ; ಸಾಂಪ್ರದಾಯಿಕವಾಗಿ ಆರೋಗ್ಯ ಮತ್ತು "
                        "ಸಂತಾನಕ್ಕೆ ಸಂಬಂಧಿಸಿದೆ. ಇದು ಸಾಂಪ್ರದಾಯಿಕ ಸೂಚಕ, "
                        "ವೈದ್ಯಕೀಯ ಅಥವಾ ಆನುವಂಶಿಕ ಪರೀಕ್ಷೆಯಲ್ಲ.",
        "title": "ಜಾತಕ ಹೊಂದಾಣಿಕೆ",
        "caption": "ಅಷ್ಟಕೂಟ (36 ಗುಣ) ಹೊಂದಾಣಿಕೆ · ಸ್ವಿಸ್ ಎಫೆಮೆರಿಸ್ · ಲಾಹಿರಿ ಅಯನಾಂಶ",
        "password": "ಪಾಸ್‌ವರ್ಡ್",
        "wrong_password": "ತಪ್ಪು ಪಾಸ್‌ವರ್ಡ್.",
        "bride": "ವಧು",
        "groom": "ವರ",
        "full_name": "ಪೂರ್ಣ ಹೆಸರು",
        "dob": "ಜನ್ಮ ದಿನಾಂಕ",
        "day": "ದಿನ",
        "month": "ತಿಂಗಳು",
        "year": "ವರ್ಷ",
        "invalid_date": "{year} {month} ತಿಂಗಳಲ್ಲಿ {day}ನೇ ದಿನಾಂಕ ಇಲ್ಲ.",
        "accuracy_q": "ಜನ್ಮ ಸಮಯ ಎಷ್ಟು ನಿಖರ?",
        "acc_exact": "ನಿಖರ (ಜನನ ಪ್ರಮಾಣಪತ್ರ / ಆಸ್ಪತ್ರೆ ದಾಖಲೆ)",
        "acc_approx_15m": "ಅಂದಾಜು (ಸುಮಾರು 15 ನಿಮಿಷಗಳೊಳಗೆ)",
        "acc_approx_1h": "ಸ್ಥೂಲ (ಸುಮಾರು ಒಂದು ಗಂಟೆಯೊಳಗೆ)",
        "acc_unknown": "ತಿಳಿದಿಲ್ಲ",
        "hour": "ಗಂಟೆ",
        "minute": "ನಿಮಿಷ",
        "AM": "AM (ಪೂರ್ವಾಹ್ನ)",
        "PM": "PM (ಅಪರಾಹ್ನ)",
        "time24": "24-ಗಂಟೆ ಸಮಯ: **{t}**{hint}",
        "hint_midnight": " (ಮಧ್ಯರಾತ್ರಿಯ ನಂತರ)",
        "hint_noon": " (ಮಧ್ಯಾಹ್ನ)",
        "manual_coords": "ಹುಡುಕುವ ಬದಲು ಅಕ್ಷಾಂಶ-ರೇಖಾಂಶವನ್ನು ಕೈಯಾರೆ ನಮೂದಿಸಿ",
        "lat": "ಅಕ್ಷಾಂಶ (ಉತ್ತರ +)",
        "lon": "ರೇಖಾಂಶ (ಪೂರ್ವ +)",
        "timezone": "ಸಮಯ ವಲಯ",
        "place_q": "ಜನ್ಮ ಸ್ಥಳ (ನಗರ ಅಥವಾ ಊರಿನ ಹೆಸರು ಮಾತ್ರ, ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಟೈಪ್ ಮಾಡಿ)",
        "place_fail": "ಸ್ಥಳ ಹುಡುಕಾಟ ವಿಫಲವಾಯಿತು. ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕ ಪರಿಶೀಲಿಸಿ, "
                      "ಅಥವಾ ಅಕ್ಷಾಂಶ-ರೇಖಾಂಶವನ್ನು ಕೈಯಾರೆ ನಮೂದಿಸಿ.",
        "choose_place": "ನಿಖರ ಸ್ಥಳವನ್ನು ಆಯ್ಕೆಮಾಡಿ",
        "no_match": "ಹೊಂದಾಣಿಕೆ ಸಿಗಲಿಲ್ಲ. ಬೇರೆ ಕಾಗುಣಿತ ಪ್ರಯತ್ನಿಸಿ (ಉದಾ. "
                    "Bengaluru / Bangalore) ಅಥವಾ ಅಕ್ಷಾಂಶ-ರೇಖಾಂಶವನ್ನು ಕೈಯಾರೆ ನಮೂದಿಸಿ.",
        "override": "UTC ಆಫ್‌ಸೆಟ್ ಬದಲಿಸಿ (ಕೆಳಗೆ ತೋರಿಸಿರುವ ಸಮಯ ವಲಯ ತಪ್ಪಾಗಿದ್ದರೆ ಮಾತ್ರ)",
        "sign": "ಚಿಹ್ನೆ",
        "hours": "ಗಂಟೆಗಳು",
        "minutes": "ನಿಮಿಷಗಳು",
        "still_needed": "ಇನ್ನೂ ಬೇಕಾಗಿರುವುದು: {items}",
        "need_name": "ಹೆಸರು",
        "need_dob": "ಜನ್ಮ ದಿನಾಂಕ",
        "need_time": "ಜನ್ಮ ಸಮಯ (ಗಂಟೆ, ನಿಮಿಷ ಮತ್ತು AM/PM)",
        "need_place": "ಜನ್ಮ ಸ್ಥಳ",
        "please_check": "**ದಯವಿಟ್ಟು ಪರಿಶೀಲಿಸಿ:** {text}",
        "when_known": "{date}, ಸ್ಥಳೀಯ ಸಮಯ {time}",
        "when_unknown": "{date}, ಸಮಯ ತಿಳಿದಿಲ್ಲ (ಚಂದ್ರನಿಗೆ ಮಧ್ಯಾಹ್ನ 12 ಬಳಸಲಾಗಿದೆ)",
        "unknown_info": "ಜನ್ಮ ಸಮಯ ತಿಳಿದಿಲ್ಲ: ಲಗ್ನವನ್ನು ಬಳಸಲಾಗುವುದಿಲ್ಲ, ಮತ್ತು "
                        "ಚಂದ್ರನನ್ನು ಇಡೀ ದಿನಕ್ಕೆ ಪರಿಶೀಲಿಸಲಾಗುತ್ತದೆ.",
        "calc_button": "ವಿವರಗಳು ಸರಿಯಾಗಿವೆ: ಹೊಂದಾಣಿಕೆ ಲೆಕ್ಕಹಾಕಿ",
        "calculating": "ಜಾತಕಗಳನ್ನು ಲೆಕ್ಕಹಾಕಲಾಗುತ್ತಿದೆ...",
        "details_changed": "ವಿವರಗಳು ಬದಲಾಗಿವೆ. ಫಲಿತಾಂಶ ನವೀಕರಿಸಲು **ಹೊಂದಾಣಿಕೆ "
                           "ಲೆಕ್ಕಹಾಕಿ** ಮತ್ತೆ ಒತ್ತಿ.",
        "score_metric": "ಗುಣ ಮಿಲನ ಅಂಕ",
        "band_label": "ಶ್ರೇಣಿ",
        "range_label": "ಸಾಧ್ಯವಿರುವ ಅಂಕಗಳ ವ್ಯಾಪ್ತಿ (ಜನ್ಮ ಸಮಯ / ಪಾದ ನಿಖರವಲ್ಲದಿದ್ದರೆ)",
        "range_value": "{a} ರಿಂದ {b}",
        "ashtakoota": "ಅಷ್ಟಕೂಟ",
        "col_koota": "ಕೂಟ",
        "col_score": "ಅಂಕ",
        "what_means": "ಪ್ರತಿ ಕೂಟದ ಅರ್ಥ",
        "doshas_header": "ದೋಷಗಳು ಮತ್ತು ಪರಿಹಾರಗಳು",
        "doshas_caption": "ಪರಿಹಾರವು 36 ಅಂಕಗಳನ್ನು ಬದಲಿಸುವುದಿಲ್ಲ; ದೋಷವನ್ನು "
                          "ಸಾಂಪ್ರದಾಯಿಕವಾಗಿ ಕಾಳಜಿಯೆಂದು ಪರಿಗಣಿಸಬೇಕೇ ಎಂಬುದನ್ನು "
                          "ಮಾತ್ರ ಬದಲಿಸುತ್ತದೆ.",
        "depends_time": "⏱️ *ನಿಖರ ಜನ್ಮ ಸಮಯ / ಪಾದವನ್ನು ಅವಲಂಬಿಸಿದೆ*",
        "parihara_applied": "*ಅನ್ವಯಿಸಿದ ಪರಿಹಾರ:*",
        "sensitivity_header": "ಜನ್ಮ ಸಮಯ / ಪಾದದ ಸೂಕ್ಷ್ಮತೆ",
        "chart_details": "ಜಾತಕದ ವಿವರಗಳು",
        "chart_of": "{name} ಅವರ ಜಾತಕ",
        "moon_label": "**ಚಂದ್ರ:** {state}",
        "col_body": "ಗ್ರಹ",
        "col_sign": "ರಾಶಿ",
        "col_degree": "ಅಂಶ",
        "col_nak": "ನಕ್ಷತ್ರ (ಪಾದ)",
        "chart_caption": "ಲಾಹಿರಿ ಅಯನಾಂಶ {aya} · {eph} · ಸಂಪೂರ್ಣ-ರಾಶಿ ಭಾವಗಳು",
        "ai_header": "ವಿವರಣೆ (AI)",
        "ai_language": "ಭಾಷೆ",
        "ai_button": "ವಿವರಣೆ ಬರೆಯಿರಿ",
        "ai_spinner": "ವಿವರಣೆ ಬರೆಯಲಾಗುತ್ತಿದೆ (ಸುಮಾರು 30 ಸೆಕೆಂಡು)...",
        "ai_caption": "ಮೇಲಿನ ಲೆಕ್ಕಾಚಾರದ ಮೌಲ್ಯಗಳಿಂದ AI ಬರೆದಿದೆ. ಕೋಷ್ಟಕ ಮತ್ತು "
                      "ದೋಷ ಫಲಿತಾಂಶಗಳೇ ಅಂತಿಮ.",
        "download": "ವರದಿ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (Markdown)",
        "footer": "ವೈಯಕ್ತಿಕ ಬಳಕೆಗಾಗಿ. ಲೆಕ್ಕಾಚಾರಗಳು ಸಾಮಾನ್ಯ ಉತ್ತರ ಭಾರತೀಯ "
                  "ಅಷ್ಟಕೂಟ ಪದ್ಧತಿಯನ್ನು ಅನುಸರಿಸುತ್ತವೆ; ಪ್ರಾದೇಶಿಕ ಸಂಪ್ರದಾಯಗಳು "
                  "ಭಿನ್ನವಾಗಿರಬಹುದು. ಜ್ಯೋತಿಷ್ಯ ಹಲವು ಅಂಶಗಳಲ್ಲಿ ಒಂದು ಮಾತ್ರ: "
                  "ಮೌಲ್ಯಗಳು, ಗೌರವ ಮತ್ತು ಸಂವಹನವೇ ಮುಖ್ಯ.",
        "md_title": "ಜಾತಕ ಹೊಂದಾಣಿಕೆ: {b} & {g}",
        "md_total": "**ಒಟ್ಟು: {total} / 36** ({band})",
        "md_range": "ಜನ್ಮ ಸಮಯದ ಅಂತರದೊಳಗೆ ಅಂಕಗಳ ವ್ಯಾಪ್ತಿ: {a}-{b}",
        "md_birth_data": "ಬಳಸಿದ ಜನ್ಮ ವಿವರಗಳು",
        "md_moon_line": "ಚಂದ್ರ: {moon}; ಲಗ್ನ: {lagna}",
        "lagna_unknown": "ತಿಳಿದಿಲ್ಲ (ಜನ್ಮ ಸಮಯ ತಿಳಿದಿಲ್ಲ)",
        "md_doshas": "ದೋಷಗಳು",
        "md_parihara": "ಪರಿಹಾರ: {p}",
        "md_interpretation": "ವಿವರಣೆ",
        "md_footer": "ಸ್ವಿಸ್ ಎಫೆಮೆರಿಸ್ (ಲಾಹಿರಿ ಅಯನಾಂಶ) ಬಳಸಿ ಲೆಕ್ಕಹಾಕಲಾಗಿದೆ. "
                     "ಜ್ಯೋತಿಷ್ಯ ಹಲವು ಅಂಶಗಳಲ್ಲಿ ಒಂದು ಮಾತ್ರ: ಮೌಲ್ಯಗಳು, ಗೌರವ "
                     "ಮತ್ತು ಸಂವಹನವೇ ಮುಖ್ಯ.",
    },
}
