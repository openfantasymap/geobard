# geobard — the talk

A short technical + ecosystem talk on **geobard**: what it does (window views,
scene Q&A, image prompts), how it works (one small OpenAI-compatible service),
and where it sits in **[GaiaWM](https://gaiawm.github.io)** as the narrative
engine behind **EyeOnWorld**.

Built with [Marp](https://marp.app/). The source of truth is a single Markdown
file plus a custom theme.

| File | Purpose |
|------|---------|
| `geobard_talk.md` | The deck — slides + speaker notes |
| `themes/cartographer.css` | Custom Marp theme — "cartographer's paper" aesthetic |
| `index.html` | Built deck (committed so GitHub Pages serves it directly) |
| `geobard_talk.pdf` | Built PDF handout |

## Build locally

No local Node toolchain required — use the official Marp Docker image:

```bash
docker run --rm -e MARP_USER=root:root -v "$PWD":/home/marp/app marpteam/marp-cli \
  geobard_talk.md --theme themes/cartographer.css \
  --html --allow-local-files -o index.html
```

Swap `--html` for `--pdf`, `--pptx`, or `--images png` for other formats.
(`MARP_USER` makes the container write files as the host user.)

Or, with a local Node 18+ install:

```bash
npx --yes @marp-team/marp-cli@4 geobard_talk.md \
  --theme themes/cartographer.css --html --allow-local-files -o index.html
```

## Publishing

The whole `docs/` folder is served by GitHub Pages (Settings → Pages → deploy
from branch, `/docs`). The landing page lives at `/`, this deck at `/talk/`.
Because `index.html` is committed, no build step runs in CI — rebuild it locally
and commit when the deck changes.
