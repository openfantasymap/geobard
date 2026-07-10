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


_VIEWPOINT_HINTS = {
    "ground": (
        "The photo is a ground-level view taken from the 'pov' point, looking "
        "along the 'bearing'. Place features to the left, centre or right of the "
        "frame, and near or far, by their position relative to the pov."
    ),
    "aerial": (
        "The photo is an overhead view of the area's 'bbox'. Place features in "
        "the frame by their coordinates (e.g. the north-west corner)."
    ),
    "oblique": (
        "The photo is an angled aerial view over the area. Reconcile features by "
        "their coordinates and their apparent depth in the frame."
    ),
}


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


def interpret_photo(
    *,
    client: OpenAI,
    model: str,
    image_url: str,
    geojson: dict[str, Any],
    viewpoint: str = "ground",
    detail_level: str = "medium",
    grounding: str = "loose",
    system: Iterable[str] | None = None,
    temperature: float = 0.7,
) -> str:
    """Interpret a photograph *through* the data describing the same area.

    The photo carries appearance (what is there, its condition, the light); the
    data carries meaning (names, types, history, custom fields). This reads one
    against the other — identifying, explaining, and reconciling — rather than
    captioning the image or narrating the data alone.

    ``model`` must be a vision-capable model. ``image_url`` may be an ``https``
    URL or a ``data:`` URL (e.g. ``data:image/jpeg;base64,...``). Returns prose.
    """
    viewpoint_hint = _VIEWPOINT_HINTS.get(viewpoint, _VIEWPOINT_HINTS["ground"])
    grounding_rule = (
        "Only mention data features you can plausibly see in the photo."
        if grounding == "strict"
        else "Prefer what you can see, but you may add nearby context from the data."
    )
    user_text = f"""\
You are looking at a photograph of a place together with structured data that
describes the SAME area. The data is your gazetteer — it names things and tells
you what they are and why they matter; the photograph shows how they look right
now. Read the photo THROUGH the data.

Rules:
- {viewpoint_hint}
- The data covers what is in and around the frame; not everything in it is
  necessarily visible, and things you can see may be absent from it — note both.
- {grounding_rule}
- Identify what is visible, explain it using the data, then add meaning the image
  alone cannot show — name, purpose, history, who holds it.
- Where the photo and the data disagree, say so, and reason about why — tentatively.
- No technical or mapping language; no coordinates or measurements.
- Treat the non-standard fields in the data as interpretive context.
- If something is unclear, stay vague rather than inventing details.
- Respond at a {detail_level} level of detail.

DATA:
{json.dumps(geojson, indent=2)}"""
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _joined(system)},
            {"role": "user", "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]},
        ],
        temperature=temperature,
    )
    return (resp.choices[0].message.content or "").strip()
