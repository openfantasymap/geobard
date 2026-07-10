"""FastAPI surface for geobard.

Four endpoints — one per LLM mode. Each request can override the model;
defaults come from env (``GEOBARD_OPENAI_MODEL``). The OpenAI client is
configured against ``GEOBARD_OPENAI_BASE_URL`` (default OpenRouter) using
``GEOBARD_OPENAI_API_KEY``.

Also exposes ``GET /healthz`` and ``GET /``.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field

from geobard import llm


class _Settings:
    def __init__(self) -> None:
        try:
            self.api_key = os.environ["GEOBARD_OPENAI_API_KEY"]
            self.model = os.environ["GEOBARD_OPENAI_MODEL"]
        except KeyError as exc:
            raise RuntimeError(f"missing required env var: {exc.args[0]}") from exc
        self.base_url = os.environ.get(
            "GEOBARD_OPENAI_BASE_URL", "https://openrouter.ai/api/v1"
        )
        self.default_temperature = float(os.environ.get("GEOBARD_TEMPERATURE", "0.7"))


@lru_cache
def _settings() -> _Settings:
    return _Settings()


@lru_cache
def _client() -> OpenAI:
    s = _settings()
    return OpenAI(api_key=s.api_key, base_url=s.base_url)
    

class WindowReq(BaseModel):
    geojson: dict[str, Any]
    system: list[str] | None = None
    detail_level: str = "medium"
    model: str | None = None
    temperature: float | None = None


class PromptReq(BaseModel):
    geojson: dict[str, Any]
    prompt: str
    system: list[str] | None = None
    model: str | None = None
    temperature: float | None = None


class ImageReq(BaseModel):
    geojson: dict[str, Any]
    image_system: list[str] | None = None
    detail_level: str = "medium"
    model: str | None = None
    temperature: float | None = None


class PhotoReq(BaseModel):
    geojson: dict[str, Any]
    image_url: str
    viewpoint: str = "ground"          # ground | aerial | oblique
    detail_level: str = "medium"
    grounding: str = "loose"           # loose | strict
    system: list[str] | None = None
    model: str | None = None           # must be a vision-capable model
    temperature: float | None = None


class TextResp(BaseModel):
    text: str = Field(description="LLM-generated prose.")
    model: str


def create_app() -> FastAPI:
    app = FastAPI(
        title="geobard",
        version="0.2.0",
        description="Turn GeoJSON into prose: window views, custom prompts, image-generation prompts, and data-driven photo interpretation.",
    )

    @app.get("/")
    def root():
        return {"service": "geobard", "version": "0.2.0", "endpoints": [
            "POST /narrate/window",
            "POST /narrate/prompt",
            "POST /narrate/photo",
            "POST /image/prompt",
            "GET  /healthz",
        ]}

    @app.get("/healthz")
    def healthz():
        # Touch settings to fail fast if env is missing.
        _settings()
        return {"status": "ok"}

    @app.post("/narrate/window", response_model=TextResp)
    def narrate_window(req: WindowReq):
        s = _settings()
        model = req.model or s.model
        try:
            text = llm.narrate_window_view(
                client=_client(), model=model, geojson=req.geojson,
                system=req.system, detail_level=req.detail_level,
                temperature=req.temperature if req.temperature is not None else s.default_temperature,
            )
        except Exception as exc:  # noqa: BLE001 — wrap upstream errors as 502
            raise HTTPException(status_code=502, detail=f"upstream LLM error: {exc}") from exc
        return TextResp(text=text, model=model)

    @app.post("/narrate/prompt", response_model=TextResp)
    def narrate_prompt(req: PromptReq):
        s = _settings()
        model = req.model or s.model
        try:
            text = llm.narrate_with_prompt(
                client=_client(), model=model, geojson=req.geojson, prompt=req.prompt,
                system=req.system,
                temperature=req.temperature if req.temperature is not None else s.default_temperature,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"upstream LLM error: {exc}") from exc
        return TextResp(text=text, model=model)

    @app.post("/image/prompt", response_model=TextResp)
    def image_prompt_endpoint(req: ImageReq):
        s = _settings()
        model = req.model or s.model
        try:
            text = llm.image_prompt(
                client=_client(), model=model, geojson=req.geojson,
                image_system=req.image_system, detail_level=req.detail_level,
                temperature=req.temperature if req.temperature is not None else s.default_temperature,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"upstream LLM error: {exc}") from exc
        return TextResp(text=text, model=model)

    @app.post("/narrate/photo", response_model=TextResp)
    def narrate_photo(req: PhotoReq):
        s = _settings()
        model = req.model or s.model
        try:
            text = llm.interpret_photo(
                client=_client(), model=model, image_url=req.image_url, geojson=req.geojson,
                viewpoint=req.viewpoint, detail_level=req.detail_level, grounding=req.grounding,
                system=req.system,
                temperature=req.temperature if req.temperature is not None else s.default_temperature,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"upstream LLM error: {exc}") from exc
        return TextResp(text=text, model=model)

    return app


app = create_app()


def main() -> None:
    import uvicorn
    uvicorn.run(
        "geobard.app:app",
        host=os.environ.get("GEOBARD_HOST", "0.0.0.0"),
        port=int(os.environ.get("GEOBARD_PORT", "8000")),
    )


if __name__ == "__main__":
    main()
