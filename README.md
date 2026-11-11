# Kundli Milan

A personal Ashtakoota (36 Guna) marriage-matching web app for you and your friends.

- **Calculations:** Swiss Ephemeris (pyswisseph), Lahiri ayanamsa, whole-sign houses
- **Covers:** all 8 kootas, Nadi / Bhakoot / Gana / Mangal Dosha with cancellation (parihara) rules, and a birth-time sensitivity check that warns when a Moon or Lagna near a boundary could change the result
- **Place lookup:** free Open-Meteo geocoding (no key), with historical timezone offsets from the IANA database and a manual override
- **Individual kundli:** choose "Individual kundli" at the top for one person's full horoscope: Rashi (D1) and Navamsa (D9) charts in South Indian style, planet table (sign, degree, nakshatra, house, retrograde, exalted / debilitated / own), Panchanga at birth (vara from sunrise, tithi, yoga, karana), Avakahada details, Mangal and Kaal Sarpa Dosha, today's Sade Sati status, and Vimshottari Mahadashas with Antardashas
- **Two ways to enter each person:** full birth date, time and place (most accurate), or just **rashi + nakshatra** (+ pada if known) for people who already know their star. The 36-point score is identical either way; Mangal Dosha then uses a "Manglik: yes / no / don't know" answer, since it needs Mars's position
- **Languages:** English and ಕನ್ನಡ (Kannada), switchable at the top right. All translations live in [kundli/i18n.py](kundli/i18n.py); add a language by adding one entry to `NAMES` and one to `STRINGS`
- **AI write-up:** optional, and off unless you add an Anthropic API key

Everything except the optional AI write-up is free.

---

## Put it online for free (Streamlit Community Cloud)

You need a free **GitHub** account. This is a one-time setup of about 15 minutes.

### 1. Put the code on GitHub

1. Sign in at https://github.com and click **New repository**.
2. Name it `kundli-milan` and choose **Public**. Streamlit's free tier needs a public repo, and that also satisfies Swiss Ephemeris's free AGPL licence. The repo holds only code, never anyone's birth data.
3. Click **uploading an existing file** and drag in everything from `D:\kundli-milan` **except** the `.venv` folder (`app.py`, `requirements.txt`, `README.md`, `.gitignore`, and the `kundli`, `tests` and `.streamlit` folders). Click **Commit changes**.

### 2. Deploy

1. Go to https://share.streamlit.io and sign in with GitHub.
2. Click **Create app**, then **Deploy a public app from GitHub**.
3. Repository: `<your-username>/kundli-milan` · Branch: `main` · Main file: `app.py`
4. Open **Advanced settings** and set **Python version to 3.11**. pyswisseph has ready-made packages only up to 3.11.
5. In the same dialog, under **Secrets**, paste:
   ```toml
   APP_PASSWORD = "pick-a-password-to-share-with-friends"
   ```
6. Click **Deploy**. After a minute or two you get a link like `https://kundli-milan.streamlit.app`.

Share that link and the password with your friends. It works on phones too.

**After pushing an update:** the app reloads its own code automatically. If it ever still shows an `ImportError`, open https://share.streamlit.io, click **⋮** next to the app and choose **Reboot**.

**Good to know:** free apps go to sleep after a few days without visitors. The next visitor sees a "wake up" button, and the app is back in about 30 seconds.

---

## Optional: AI write-up (not free)

The app works fully without this. If you want an AI-written explanation in English, Hindi, Kannada, Tamil and other languages:

1. Create an API key at https://console.anthropic.com and add some credit. This is billed per use and separate from any Claude Pro subscription.
2. Add it to the app's **Secrets**:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   # Optional cheaper model; the default is claude-opus-5-5:
   # ANTHROPIC_MODEL = "claude-haiku-5-5"
   ```
Rough cost per report: under $0.01 with Haiku, about $0.05-0.10 with the default. The AI receives only the calculated results and first names, never birth dates, times or places.

---

## Run it on your own PC

```bash
cd D:\kundli-milan
.venv\Scripts\streamlit run app.py
```
Then open http://localhost:8501. Run the self-tests with `.venv\Scripts\python -m pytest`.

---

## Accuracy notes

- **Check the "Please check" line** under each person before calculating. The most common cause of wrong results is a wrong UTC offset, not the astronomy. Births in Mumbai before 1955 or Kolkata before 1948 may have been recorded in local time (Bombay Time UTC+04:51, Calcutta Time UTC+05:53:20). Use the override if so.
- **Unknown birth time:** the Moon is checked across the whole day and the Lagna isn't used. Mangal Dosha is then judged from the Moon and Venus only.
- **Traditions differ.** The Vashya and Gana scoring tables and the Mangal Dosha house list (with or without the 2nd house) vary between regions and texts. They're marked `VARIANT` in [kundli/data.py](kundli/data.py), so you can match your family astrologer's practice.
- **Ephemeris precision:** without extra data files the app uses Swiss Ephemeris's built-in Moshier model, which is accurate to a few arc-seconds. That is far finer than a nakshatra pada (3°20'). For full JPL-level precision, put `sepl_18.se1` and `semo_18.se1` from https://github.com/aloistr/swisseph/tree/master/ephe in an `ephe/` folder.
- Astrology is one input among many. Values, respect and communication matter most.
