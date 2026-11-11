"""Optional AI interpretation. Only runs when ANTHROPIC_API_KEY is configured.

The model receives the calculated fact sheet only (no birth date, time or
place) and is told never to compute or change any value. A light check then
confirms the total score it mentions matches the engine's.
"""
from __future__ import annotations

import json
import re

import anthropic

DEFAULT_MODEL = "claude-opus-5-5"
# Models that support the server-side refusal fallback.
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5",
                    "claude-fable-5-2", "claude-fable-5-1"}

SYSTEM_PROMPT = """You write warm, balanced Kundli Milan (Vedic horoscope matching) reports for friends and family.

You receive a JSON fact sheet produced by a Swiss Ephemeris calculation engine. Rules:
- Use ONLY the values in the fact sheet. Never recompute, round differently, change or invent any score, nakshatra, sign, nadi, gana or dosha status.
- Structure: a short overview with the total score; one short paragraph per koota (what it measures and what this couple's result suggests); then each dosha with its status and any cancellation rules exactly as given; then birth-time sensitivity notes if any exist.
- Tone: kind, practical and never fatalistic. Do not predict death, divorce, widowhood or illness. Never tell anyone not to marry.
- Varna is about temperament, not caste. Nadi is a traditional indicator, not a medical or genetic test.
- Do not prescribe gemstones, costly rituals or pujas. You may suggest discussing doshas with a trusted family astrologer.
- End with one sentence noting that astrology is one input among many, and that values, respect and communication matter most.
- Write in {language}. Use Markdown headings. Keep it under 700 words."""


class AIError(Exception):
    pass


def generate_interpretation(facts: dict, api_key: str, model: str = DEFAULT_MODEL,
                            language: str = "English") -> tuple[str, list[str]]:
    """Returns (markdown_text, warnings)."""
    client = anthropic.Anthropic(api_key=api_key)
    request = dict(
        model=model,
        max_tokens=8000,
        system=SYSTEM_PROMPT.format(language=language),
        messages=[{
            "role": "user",
            "content": "Fact sheet:\n```json\n"
                       + json.dumps(facts, indent=2, ensure_ascii=False)
                       + "\n```\nWrite the report.",
        }],
    )
    try:
        if model in _FALLBACK_MODELS:
            resp = client.beta.messages.create(
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                **request,
            )
        else:
            resp = client.messages.create(**request)
    except anthropic.AuthenticationError as e:
        raise AIError("The Anthropic API key was rejected.") from e
    except anthropic.RateLimitError as e:
        raise AIError("Rate limited by the Anthropic API; try again in a minute.") from e
    except anthropic.APIStatusError as e:
        raise AIError(f"Anthropic API error {e.status_code}: {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise AIError("Could not reach the Anthropic API.") from e

    if resp.stop_reason == "refusal":
        raise AIError("The model declined to write this report.")

    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    warnings = []
    if resp.stop_reason == "max_tokens":
        warnings.append("The write-up was cut off before it finished.")
    warnings += check_numbers(text, facts)
    return text, warnings


def check_numbers(text: str, facts: dict) -> list[str]:
    """Flag any 'X/36' or 'X out of 36' that disagrees with the engine."""
    total = float(facts["total_score"])
    allowed = {total, 36.0} | set(facts.get("score_range_within_birth_time_window") or [])
    found = re.findall(r"(\d+(?:\.\d+)?)\s*(?:/|out of)\s*36", text)
    bad = sorted({f for f in found
                  if all(abs(float(f) - a) > 1e-9 for a in allowed)})
    if bad:
        return [f"The write-up mentions {', '.join(bad)}/36 but the calculated "
                f"total is {total:g}/36. Trust the table, not the text."]
    return []
