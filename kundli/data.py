"""Static Vedic astrology tables used by the matching engine.

Index conventions (0-based everywhere in code):
  nakshatra 0 = Ashwini ... 26 = Revati
  rashi     0 = Mesha (Aries) ... 11 = Meena (Pisces)

Tables marked VARIANT differ between traditions / software. They follow the
most common North Indian Ashtakoota usage. If your family astrologer follows a
different text, change the table here; nothing else needs to change.
"""

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
]

RASHIS = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)",
    "Karka (Cancer)", "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)",
    "Vrishchika (Scorpio)", "Dhanu (Sagittarius)", "Makara (Capricorn)",
    "Kumbha (Aquarius)", "Meena (Pisces)",
]

RASHI_LORD = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]

# ---------------------------------------------------------------- 1. Varna (1)
# Moon sign -> varna rank. Water=Brahmin(4), Fire=Kshatriya(3),
# Earth=Vaishya(2), Air=Shudra(1). Groom's rank >= bride's rank scores 1.
VARNA_NAMES = {4: "Brahmin", 3: "Kshatriya", 2: "Vaishya", 1: "Shudra"}
RASHI_VARNA = [3, 2, 1, 4, 3, 2, 1, 4, 3, 2, 1, 4]

# --------------------------------------------------------------- 2. Vashya (2)
VASHYA_CLASSES = [
    "Chatushpada (quadruped)", "Manava (human)", "Jalachara (water)",
    "Vanachara (wild)", "Keeta (insect)",
]
CHATUSHPADA, MANAVA, JALACHARA, VANACHARA, KEETA = range(5)

# Sagittarius and Capricorn are split at 15 degrees (handled in vashya_class).
_RASHI_VASHYA = [
    CHATUSHPADA, CHATUSHPADA, MANAVA, JALACHARA, VANACHARA, MANAVA,
    MANAVA, KEETA, None, None, MANAVA, JALACHARA,
]


def vashya_class(sidereal_moon_lon: float) -> int:
    rashi = int(sidereal_moon_lon // 30) % 12
    deg = sidereal_moon_lon % 30
    if rashi == 8:   # Dhanu: first half human, second half quadruped
        return MANAVA if deg < 15 else CHATUSHPADA
    if rashi == 9:   # Makara: first half quadruped, second half water
        return CHATUSHPADA if deg < 15 else JALACHARA
    return _RASHI_VASHYA[rashi]


# VARIANT. VASHYA_SCORE[groom_class][bride_class]; symmetric here.
VASHYA_SCORE = [
    #  Chat  Man  Jal  Van  Keeta
    [2.0, 1.0, 1.0, 0.5, 1.0],  # Chatushpada
    [1.0, 2.0, 0.5, 0.0, 1.0],  # Manava
    [1.0, 0.5, 2.0, 1.0, 1.0],  # Jalachara
    [0.5, 0.0, 1.0, 2.0, 0.0],  # Vanachara
    [1.0, 1.0, 1.0, 0.0, 2.0],  # Keeta
]

# ----------------------------------------------------------------- 3. Tara (3)
# Count (inclusive) from one nakshatra to the other, remainder after /9.
TARA_NAMES = {
    1: "Janma", 2: "Sampat", 3: "Vipat", 4: "Kshema", 5: "Pratyak",
    6: "Sadhana", 7: "Naidhana", 8: "Mitra", 0: "Parama Mitra",
}
BAD_TARA_REMAINDERS = {3, 5, 7}

# ----------------------------------------------------------------- 4. Yoni (4)
YONI_ANIMALS = [
    "Horse", "Elephant", "Sheep", "Serpent", "Dog", "Cat", "Rat", "Cow",
    "Buffalo", "Tiger", "Deer", "Monkey", "Mongoose", "Lion",
]
NAK_YONI = [0, 1, 2, 3, 3, 4, 5, 2, 5, 6, 6, 7, 8, 9, 8, 9, 10, 10, 4, 11,
            12, 11, 13, 0, 13, 7, 1]
NAK_YONI_GENDER = "MMFMFFFMMMFMFFMMFMMMMFFFMFF"

YONI_SCORE = [
    # Hor Ele She Ser Dog Cat Rat Cow Buf Tig Dee Mon Mgo Lio
    [4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 3, 3, 2, 1],  # Horse
    [2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0],  # Elephant
    [2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1],  # Sheep
    [3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2],  # Serpent
    [2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1],  # Dog
    [2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 1],  # Cat
    [2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2],  # Rat
    [1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1],  # Cow
    [0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 1],  # Buffalo
    [1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1],  # Tiger
    [3, 2, 2, 2, 0, 3, 2, 3, 2, 1, 4, 2, 2, 1],  # Deer
    [3, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2],  # Monkey
    [2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2],  # Mongoose
    [1, 0, 1, 2, 1, 1, 2, 1, 1, 1, 1, 2, 2, 4],  # Lion
]
SWORN_ENEMY_YONIS = [
    ("Horse", "Buffalo"), ("Elephant", "Lion"), ("Sheep", "Monkey"),
    ("Serpent", "Mongoose"), ("Dog", "Deer"), ("Cat", "Rat"), ("Cow", "Tiger"),
]

# --------------------------------------------------------- 5. Graha Maitri (5)
# Naisargika (natural) friendships.
FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon", "Mars"},
}
# Points by the pair of one-way relationships (sorted).
MAITRI_POINTS = {
    ("friend", "friend"): 5.0,
    ("friend", "neutral"): 4.0,
    ("neutral", "neutral"): 3.0,
    ("enemy", "friend"): 1.0,
    ("enemy", "neutral"): 0.5,
    ("enemy", "enemy"): 0.0,
}

# ----------------------------------------------------------------- 6. Gana (6)
GANA_NAMES = ["Deva", "Manushya", "Rakshasa"]
NAK_GANA = [0, 1, 2, 1, 0, 1, 0, 0, 2, 2, 1, 1, 0, 2, 0, 2, 0, 2, 2, 1, 1, 0,
            2, 2, 1, 1, 0]
# VARIANT. GANA_SCORE[groom_gana][bride_gana]
GANA_SCORE = [
    # bride: Deva Manushya Rakshasa
    [6.0, 6.0, 1.0],  # groom Deva
    [5.0, 6.0, 0.0],  # groom Manushya
    [1.0, 0.0, 6.0],  # groom Rakshasa
]

# -------------------------------------------------------------- 7. Bhakoot (7)
# Distance of groom's Moon sign counted from bride's (1..12).
BAD_BHAKOOT = {2, 12, 5, 9, 6, 8}
BHAKOOT_LABEL = {1: "1/1", 7: "7/7", 2: "2/12", 12: "2/12", 3: "3/11",
                 11: "3/11", 4: "4/10", 10: "4/10", 5: "5/9", 9: "5/9",
                 6: "6/8", 8: "6/8"}

# ----------------------------------------------------------------- 8. Nadi (8)
NADI_NAMES = ["Aadi (Vata)", "Madhya (Pitta)", "Antya (Kapha)"]
_NADI_CYCLE = [0, 1, 2, 2, 1, 0]


def nadi_of(nakshatra: int) -> int:
    return _NADI_CYCLE[nakshatra % 6]


# --------------------------------------------------------------- Score bands
SCORE_BANDS = [
    (0.0, 18.0, "Below 18: traditionally not recommended"),
    (18.0, 25.0, "18-24: average / acceptable"),
    (25.0, 33.0, "25-32: very good"),
    (33.0, 36.01, "33-36: excellent"),
]


def score_band(total: float) -> str:
    for lo, hi, label in SCORE_BANDS:
        if lo <= total < hi:
            return label
    return SCORE_BANDS[-1][2]


# ------------------------------------------------------------- Mangal Dosha
# VARIANT: South Indian practice includes house 2; many North Indian texts use
# only 1, 4, 7, 8, 12. Remove 2 here if you follow the latter.
MANGLIK_HOUSES = (1, 2, 4, 7, 8, 12)
MARS_OWN_OR_EXALTED = {0: "own sign", 7: "own sign", 9: "exaltation sign"}
# house -> Mars signs for which that house placement is traditionally exempt
MANGLIK_HOUSE_SIGN_EXCEPTIONS = {
    2: {2, 5},    # Gemini, Virgo
    4: {0, 7},    # Aries, Scorpio
    7: {3, 9},    # Cancer, Capricorn
    8: {8, 11},   # Sagittarius, Pisces
    12: {1, 6},   # Taurus, Libra
}
