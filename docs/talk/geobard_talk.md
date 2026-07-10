---
marp: true
theme: cartographer
paginate: true
size: 16:9
header: "geobard · turn GeoJSON into prose"
footer: "Open Fantasy Map · part of GaiaWM"
---

<!--
============================================================
geobard — turn GeoJSON into prose
A short technical + ecosystem talk.

Build:
  docker run --rm -e MARP_USER=root:root -v "$PWD":/home/marp/app \
    marpteam/marp-cli geobard_talk.md \
    --theme themes/cartographer.css --html --allow-local-files -o index.html

Swap --html for --pdf / --pptx / "--images png" for other formats.
============================================================
-->

<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _footer: "github.com/openfantasymap/geobard" -->

<span class="tick">Open-source · FastAPI · OpenAI-compatible</span>

# Turn GeoJSON<br>into <em>prose</em>.

A small service that reads a map scene and writes what you'd see standing in it.

<!--
SPEAKER:
- One-liner: "geobard takes the data behind a map and hands back human language."
- Set up the whole talk: 3 modes, how it works, where it lives in GaiaWM.
- This is deliberately a *small* tool — the value is in the prompting, not the size.
-->

---

<!-- _class: dark -->

## A map is data. A place is a feeling.

A `FeatureCollection` is precise and machine-readable — and says nothing about
**what it's like to be there.**

- Coordinates, types, names, geometry
- No "you're standing at the edge of a market square at first light"
- Players, agents, and readers want the **place**, not the table

**geobard is the thin layer that closes that gap.**

<!--
SPEAKER:
- The gap: GIS gives you truth; narration gives you presence.
- Same problem whether the consumer is a human reader or an AI agent that needs grounding.
- Tease: we solve it with careful prompting over any chat model.
-->

---

## One small service. Four modes.

geobard is a thin, well-prompted layer between **your map data** and **a language model.**

<div class="columns-3">
<div class="box">

### 👁️ Window view
Describe the scene as if you stand in it. Human language only.

<span class="endpoint">POST /narrate/window</span>
</div>
<div class="box">

### 💬 Ask the scene
Answer a question grounded in what's actually present.

<span class="endpoint">POST /narrate/prompt</span>
</div>
<div class="box">

### 🎨 Image prompt
Rewrite the scene as a prompt for an image model.

<span class="endpoint">POST /image/prompt</span>
</div>
</div>

<br>

**Three modes generate from data.** A fourth — `/narrate/photo` — reads a real
photo *through* it (coming up). Every call can override `model` and `temperature`.

<!--
SPEAKER:
- Emphasise smallness: four endpoints, two source files (app.py + llm.py).
- The LLM helpers are pure functions — importable directly into other services.
- The fourth mode is the only multimodal one; the other three are data-only.
-->

---

## Mode 1 — the window view

<div class="columns">
<div>

**In:** a scene with a point of view, bearing, time of day, features.

```json
{
  "geojson": {
    "pov": {"lat": 44.49, "lng": 11.34},
    "bearing": 90,
    "time_of_day": "07:30",
    "features": [
      {"properties": {
        "type": "buildings",
        "name": "market hall"}}
    ]
  },
  "detail_level": "medium"
}
```
</div>
<div>

**Out:** prose, no map-speak.

> You're looking east into the early light. Just <span class="loc">across the way</span> the old market hall squares off against the morning, its long roofline catching the first of the sun while the street in front is still half in shade.

<span class="tick">distance in human terms · vague where the data is</span>
</div>
</div>

<!--
SPEAKER:
- The rules baked into the prompt: no coordinates, no measurements; near / across the street / to the left;
  stay vague rather than invent; 1-2 paragraphs; read non-standard fields as context.
- detail_level: low | medium | high tunes verbosity.
-->

---

## Mode 2 — ask the scene

Pass a `prompt` alongside the scene. The model reasons over **what's present** —
and stays honest about what isn't.

<div class="columns">
<div>

```json
{
  "geojson": { "...": "..." },
  "prompt": "What's the quickest
             way out on foot?"
}
```

<span class="tick">grounded · conversational · 1–2 paragraphs</span>
</div>
<div>

> From here your fastest line is to keep the market hall on your left and follow
> the lane it fronts onto — it bends toward the open ground you can just make out
> ahead, away from the tighter streets behind you.
</div>
</div>

<!--
SPEAKER:
- Same grounding rules as window view, but goal-directed.
- This is the mode that matters most for AI agents: spatial Q&A over a scene.
-->

---

## Mode 3 — the image prompt

Same scene, retargeted for an **image-generation model** — architecture and
city structure first, so the render is faithful to the *place*.

```text
Ground-level view looking east at dawn down a cobbled market street.
A long stone market hall dominates the right, its arcaded façade and
pitched roof catching low golden light; narrow row houses recede on
the left into soft morning shade. Medieval European town, wide-angle,
photographic, soft volumetric light.
```

<span class="tick">image_system[] adds style hints · detail_level tunes density</span>

<!--
SPEAKER:
- System prompt frames the model as a prompt engineer for an image LLM.
- "The city structure is paramount" — we deliberately drop incidental features.
- Output feeds straight into SDXL / Flux / DALL·E / Midjourney-style tools.
-->

---

## Mode 4 — read a photo *through* its data

A real **photo** carries appearance; the **data** carries meaning. Interpret one
against the other — don't caption, and don't narrate the data alone.

<div class="columns">
<div>

```json
{
  "geojson":   { "...same area..." },
  "image_url": "https://…/tower.jpg",
  "viewpoint": "ground",
  "grounding": "loose"
}
```

<span class="tick">identify → explain → reconcile · needs a vision model · new in 0.2</span>
</div>
<div>

> The leaning tower on your left is the old **Harper watchpost**. The record
> remembers it as a lookout over the river road — but the boarded windows and the
> ivy tell a plainer story: <span class="loc">no one has watched here in years.</span>
</div>
</div>

<!--
SPEAKER:
- The signature move is *reconciliation*: data says "active watchpost", the photo
  shows a ruin → interpret the gap, tentatively.
- viewpoint (ground / aerial / oblique) tells the model how photo and data register.
- grounding: strict = only what's visible; loose = may add nearby context. Honest either way.
- This is the multimodal sibling of /narrate/window: window imagines a view from
  data; photo interprets a real one.
-->

---

## How it works

```
GeoJSON scene  ──▶   geobard   ──▶   prose / image-prompt
  features            mode-specific        { "text": "…",
  pov, bearing        system + user          "model": "…" }
  time_of_day         prompt → chat
  custom props        completion
```

- **No magic** — careful per-mode prompts do the translation, the model writes
- **Non-standard GeoJSON fields** are read as extra context, not ignored
- Pure functions over `(geojson, options, client)` — framework-free, reusable

<!--
SPEAKER:
- llm.py holds the prompt logic; app.py is just the FastAPI surface.
- Because the helpers are decoupled, another service can import them directly.
- Upstream model errors are wrapped as HTTP 502.
-->

---

## Bring your own model

geobard speaks the **OpenAI chat-completions API** — so it runs against whatever
you already use.

| | |
|---|---|
| **Default** | OpenRouter (`https://openrouter.ai/api/v1`) |
| **Swap** | set `GEOBARD_OPENAI_BASE_URL` |
| **Works with** | OpenAI · Ollama · Groq · Together · any compatible endpoint |
| **Per request** | override `model` and `temperature` |

<span class="tick">local with Ollama · hosted with OpenRouter · pick per call</span>

<!--
SPEAKER:
- Cost/latency knob: cheap fast models (Haiku) for window views, bigger for Q&A.
- Self-host the whole loop with Ollama for offline / private worlds.
-->

---

## The API surface

| Route | Does |
|---|---|
| <span class="endpoint">POST /narrate/window</span> | Window view. `geojson`, `system[]`, `detail_level` → `{text, model}` |
| <span class="endpoint">POST /narrate/prompt</span> | Answer a `prompt` about the scene |
| <span class="endpoint">POST /narrate/photo</span> | Interpret an `image_url` through same-area data (vision model) |
| <span class="endpoint">POST /image/prompt</span> | Image-gen prompt; `image_system[]` style hints |
| <span class="endpoint">GET&nbsp;&nbsp;/healthz</span> | `{"status":"ok"}` once env is valid (Docker healthcheck) |

All bodies take optional `model` and `temperature`. Narration modes accept
`system[]` prompt lines; window, image & photo modes take `detail_level`.

<!--
SPEAKER:
- GET / returns a small service descriptor listing the endpoints.
- Pydantic models validate every request body.
-->

---

## Running in two commands

<div class="columns">
<div>

**1 · start the service**

```bash
docker run --rm -p 8000:8000 \
  -e GEOBARD_OPENAI_API_KEY=sk-or-… \
  -e GEOBARD_OPENAI_MODEL=\
anthropic/claude-haiku-4.5 \
  ghcr.io/openfantasymap/geobard:latest
```
</div>
<div>

**2 · narrate a scene**

```bash
curl -sS \
  localhost:8000/narrate/window \
  -H "content-type: application/json" \
  -d '{ "geojson": { … },
        "detail_level": "medium" }'
# → { "text": "…", "model": "…" }
```
</div>
</div>

<span class="tick">image: ghcr.io/openfantasymap/geobard · MIT or Apache-2.0</span>

<!--
SPEAKER:
- Two required env vars: API key + default model. Everything else has defaults.
- Also: pip install -e .[test] && uvicorn geobard.app:app --reload for dev.
-->

---

## Configuration

| Env | Required | Default |
|---|---|---|
| `GEOBARD_OPENAI_API_KEY` | yes | — |
| `GEOBARD_OPENAI_MODEL` | yes | — |
| `GEOBARD_OPENAI_BASE_URL` | no | `openrouter.ai/api/v1` |
| `GEOBARD_TEMPERATURE` | no | `0.7` |
| `GEOBARD_HOST` / `GEOBARD_PORT` | no | `0.0.0.0` / `8000` |

Fail-fast: `/healthz` touches settings, so a missing key surfaces immediately.

<!--
SPEAKER:
- Keep this brief — it's a reference slide. Move quickly to the ecosystem.
-->

---

<!-- _class: dark -->

## Where geobard lives: GaiaWM

**GaiaWM** is world infrastructure for AI — a simulation-intelligence platform
that layers space, time, society and causal influence over 40+ canonical worlds.

<div class="stack">
<div class="layer"><div class="nm">🗺️ Spatial</div><div class="ds">40+ worlds, GIS precision — Toril, Star Wars, Middle-earth</div></div>
<div class="layer"><div class="nm">⏰ Temporal</div><div class="ds">Time-aware state — history, seasons, cycles</div></div>
<div class="layer"><div class="nm">👥 Social</div><div class="ds">Factions, relationships, reputation</div></div>
<div class="layer"><div class="nm">🌊 Influence</div><div class="ds">Causal simulation — channels &amp; propagation</div></div>
<div class="layer hl"><div class="nm">🧠 Narration → geobard</div><div class="ds">Perception &amp; description — geobard &amp; EyeOnWorld</div></div>
</div>

<!--
SPEAKER:
- geobard is one layer of the stack: the *narration* layer.
- Everything below produces structured world state; geobard makes it legible.
- geobard and EyeOnWorld are the same narration capability (gaia/llm.py): geobard is the
  standalone open-source service, EyeOnWorld the live map product.
-->

---

<!-- _class: dark -->

## geobard & EyeOnWorld — one engine

> Click any location on the map — get an immersive description of standing there.

<div class="columns">
<div>

**EyeOnWorld** (live on **openfantasymaps.org**) is the same narration — geobard's
window view — wired to real world data:

- Map tile → GeoJSON scene → `/narrate/window`
- The same `/image/prompt` mode renders the view
- Agents use `/narrate/prompt` to **reason over a place**
</div>
<div>

> Looking around, you're standing at the edge of a residential neighborhood where
> the midday sun beats down on the cobblestones. <span class="loc">Selduth
> Street</span> is just a few paces to your right…
<cite>EyeOnWorld · generated from Waterdeep map data</cite>
</div>
</div>

<!--
SPEAKER:
- This is the proof: it's the same narration capability, in production.
- geobard is the standalone open-source service; EyeOnWorld is it live on the map.
- The narration layer turns GaiaWM's structured truth into something a person reads
  and an agent can act on.
-->

---

## Integrate it

- **As a service** — `docker run`, POST your scenes, get text back
- **As a library** — import the pure helpers from `geobard.llm` directly
- **In an agent loop** — `/narrate/prompt` gives spatial grounding over a scene
- **In a pipeline** — `/image/prompt` → your image model of choice
- **Self-hosted & private** — point the base URL at a local Ollama

<br>

**Small surface, few dependencies** — FastAPI, Pydantic, the OpenAI client.

<!--
SPEAKER:
- Pitch the two integration shapes: HTTP service vs. direct import.
- Stress it composes — it's a building block, not a platform.
-->

---

<!-- _class: lead -->
<!-- _class: dark -->
<!-- _footer: "gaiawm.github.io · openfantasymaps.org · github.com/openfantasymap/geobard" -->

<span class="tick">geobard</span>

# A scene goes in.<br><em>Words</em> come out.

The open-source narration engine from GaiaWM — the engine behind EyeOnWorld.

**github.com/openfantasymap/geobard** · MIT or Apache-2.0

<!--
SPEAKER:
- Recap the arc: data → presence; three modes; any backend; the narrative layer of GaiaWM.
- Call to action: try the Docker image, or see EyeOnWorld live on openfantasymaps.org.
-->
