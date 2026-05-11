"""LLM helpers — pure functions over (geojson, options, client).

These are intentionally decoupled from any web framework so they can be
imported directly into other services. The FastAPI surface lives in
``geobard.app``.
"""
from __future__ import annotations

import json
from typing import Any, Iterable

from openai import OpenAI


def chat(client: OpenAI, model: str, system: str, user: str, temperature: float = 0.7) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=temperature,
    )
    return (resp.choices[0].message.content or "").strip()


def _joined(lines: Iterable[str] | None) -> str:
    return "\n".join(lines or [])


def narrate_window_view(
    *,
    client: OpenAI,
    model: str,
    geojson: dict[str, Any],
    system: Iterable[str] | None = None,
    detail_level: str = "medium",
    temperature: float = 0.7,
) -> str:
    """Describe a GeoJSON scene as if seen through a window. Returns prose."""
    user_prompt = f"""\
The information below describes what surrounds you.
Describe what you see as if speaking naturally to another person.

Rules:
- No technical or mapping language
- No coordinates or measurements
- Use visual, spatial, and sensory cues
- Describe distance in human terms (near, across the street, farther away, to the left, to the right)
- If something is unclear, stay vague rather than inventing details
- 1–2 paragraphs, conversational tone
- In the geojson file use the non-standard fields as context for the description of the data.
- describe the context before the description
- The description should be at a {detail_level} level of detail.

DATA:
{json.dumps(geojson, indent=2)}"""
    return chat(client, model, _joined(system), user_prompt, temperature)


def narrate_with_prompt(
    *,
    client: OpenAI,
    model: str,
    geojson: dict[str, Any],
    prompt: str,
    system: Iterable[str] | None = None,
    temperature: float = 0.7,
) -> str:
    """Answer ``prompt`` about a GeoJSON scene. Returns prose."""
    user_prompt = f"""\
The information below describes what surrounds you.

Rules:
- No technical or mapping language
- Use visual, spatial, and sensory cues
- Describe distance in human terms (near, across the street, farther away, to the left, to the right)
- If something is unclear, stay vague rather than inventing details
- 1–2 short paragraphs, conversational tone
- In the geojson file use the non-standard fields as context for the description of the data.
- describe the context before the description

DATA:
{json.dumps(geojson, indent=2)}

QUESTION:
{prompt}"""
    return chat(client, model, _joined(system), user_prompt, temperature)


def image_prompt(
    *,
    client: OpenAI,
    model: str,
    geojson: dict[str, Any],
    image_system: Iterable[str] | None = None,
    detail_level: str = "medium",
    temperature: float = 0.7,
) -> str:
    """Turn a GeoJSON scene into a prompt for an image-generation LLM."""
    system_prompt = (
        "you are an efficient prompt engineer and need to describe a data object "
        "in a way that an image generation llm can create the image for us."
    )
    user_prompt = f"""\
The information below describes what can be seen.
Describe what you would see as a person standing in the geojson "pov" point on the ground in a way that an llm can generate an accurate image.
{_joined(image_system)}
You don't need to have everything in the scene: the important elements are the architectural and urbanistic elements.
The city structure is paramount.
Describe at a {detail_level} level of detail.

DATA:
{json.dumps(geojson, indent=2)}"""
    return chat(client, model, system_prompt, user_prompt, temperature)
