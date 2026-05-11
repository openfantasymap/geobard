# geobard

[![ci](https://github.com/openfantasymap/geobard/actions/workflows/ci.yml/badge.svg)](https://github.com/openfantasymap/geobard/actions/workflows/ci.yml)
[![docker](https://github.com/openfantasymap/geobard/actions/workflows/docker.yml/badge.svg)](https://github.com/openfantasymap/geobard/actions/workflows/docker.yml)
[![license](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue)](#license)

**Turn GeoJSON into prose.** A small FastAPI service that takes a GeoJSON
description of a scene and asks an LLM to produce one of three things:

- **A window view** — natural-language description, as if you were standing there.
- **An answer to a question** — pass a `prompt` along with the scene.
- **An image-generation prompt** — text suitable for feeding to an image model.

geobard speaks the OpenAI chat-completions API, so it works with OpenAI
directly, OpenRouter, Ollama, Groq, Together, or any other compatible
backend. OpenRouter is the default.

## Quick start

```bash
docker run --rm -p 8000:8000 \
  -e GEOBARD_OPENAI_API_KEY=sk-or-... \
  -e GEOBARD_OPENAI_MODEL=anthropic/claude-haiku-4.5 \
  ghcr.io/openfantasymap/geobard:latest
```

```bash
curl -sS http://localhost:8000/narrate/window \
  -H "content-type: application/json" \
  -d '{
        "geojson": {
          "type": "FeatureCollection",
          "pov": {"lat": 44.49, "lng": 11.34},
          "bearing": 90,
          "time_of_day": "07:30",
          "features": [
            {"type":"Feature","properties":{"type":"buildings","name":"market hall"},"geometry":{"type":"Point","coordinates":[11.341,44.490]}}
          ]
        },
        "detail_level": "medium",
        "system": ["You narrate a Forgotten Realms scene."]
      }'
```

## API

### `POST /narrate/window`

Generic window view. Body:

```json
{
  "geojson":      {<feature collection>},
  "system":       ["optional", "system", "prompt", "lines"],
  "detail_level": "low | medium | high",
  "model":        "anthropic/claude-haiku-4.5",   // optional override
  "temperature":  0.7                              // optional override
}
```

Returns `{"text": "...", "model": "..."}`.

### `POST /narrate/prompt`

Custom question about the scene. Body:

```json
{
  "geojson": {<feature collection>},
  "prompt":  "What's the easiest way out of here on foot?",
  "system":  ["optional"],
  "model":   "...",
  "temperature": 0.7
}
```

### `POST /image/prompt`

Produces a prompt suitable for an image-generation model. Body:

```json
{
  "geojson":      {<feature collection>},
  "image_system": ["optional", "style", "hints"],
  "detail_level": "medium",
  "model":        "...",
  "temperature":  0.7
}
```

### `GET /healthz`

Returns `{"status": "ok"}` once env is validated. Used by Docker healthcheck.

## Configuration

| Env | Required | Default | Purpose |
|---|---|---|---|
| `GEOBARD_OPENAI_API_KEY` | yes | — | OpenAI-compatible API key. |
| `GEOBARD_OPENAI_MODEL` | yes | — | Default model id (overridable per request). |
| `GEOBARD_OPENAI_BASE_URL` | no | `https://openrouter.ai/api/v1` | Override for any OpenAI-compatible endpoint. |
| `GEOBARD_TEMPERATURE` | no | `0.7` | Default sampling temperature. |
| `GEOBARD_HOST` | no | `0.0.0.0` | Bind address. |
| `GEOBARD_PORT` | no | `8000` | Bind port. |

## Development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e .[test]
pytest
uvicorn geobard.app:app --reload
```

## License

Dual-licensed under either of MIT or Apache-2.0, at your option.
