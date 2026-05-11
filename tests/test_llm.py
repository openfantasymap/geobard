"""Pure-prompt-construction tests — no LLM call required.

We stub the OpenAI client and assert the messages it would have received.
"""
import json
from unittest.mock import MagicMock

import pytest

from geobard import llm


def _stub_client(return_text: str = "ok"):
    client = MagicMock()
    choice = MagicMock()
    choice.message.content = return_text
    resp = MagicMock()
    resp.choices = [choice]
    client.chat.completions.create.return_value = resp
    return client


def _captured(client):
    """Return the kwargs that were passed to chat.completions.create."""
    return client.chat.completions.create.call_args.kwargs


def test_narrate_window_view_calls_with_system_and_user():
    client = _stub_client("a quiet morning street")
    result = llm.narrate_window_view(
        client=client,
        model="claude-haiku-4.5",
        geojson={"type": "FeatureCollection", "features": []},
        system=["You narrate a fantasy scene."],
        detail_level="medium",
    )
    assert result == "a quiet morning street"
    kw = _captured(client)
    assert kw["model"] == "claude-haiku-4.5"
    msgs = kw["messages"]
    assert msgs[0]["role"] == "system"
    assert "fantasy scene" in msgs[0]["content"]
    assert msgs[1]["role"] == "user"
    assert "medium level of detail" in msgs[1]["content"]
    assert "FeatureCollection" in msgs[1]["content"]


def test_narrate_with_prompt_embeds_question():
    client = _stub_client("south, along the river")
    llm.narrate_with_prompt(
        client=client,
        model="m",
        geojson={},
        prompt="which way is the river?",
        system=["context"],
    )
    user = _captured(client)["messages"][1]["content"]
    assert "QUESTION:\nwhich way is the river?" in user


def test_image_prompt_uses_image_system():
    client = _stub_client("a cobbled square at dawn")
    llm.image_prompt(
        client=client,
        model="m",
        geojson={"pov": {"lat": 1, "lng": 2}},
        image_system=["photoreal", "morning fog"],
        detail_level="high",
    )
    msgs = _captured(client)["messages"]
    assert "prompt engineer" in msgs[0]["content"]
    user = msgs[1]["content"]
    assert "photoreal" in user
    assert "morning fog" in user
    assert "high level of detail" in user


def test_no_system_lines_yields_empty_system():
    client = _stub_client("ok")
    llm.narrate_window_view(client=client, model="m", geojson={})
    assert _captured(client)["messages"][0]["content"] == ""


def test_geojson_serialised_into_user_message():
    client = _stub_client("ok")
    payload = {"odd_key": [1, 2, 3], "nested": {"inner": True}}
    llm.narrate_window_view(client=client, model="m", geojson=payload)
    user = _captured(client)["messages"][1]["content"]
    assert json.dumps(payload, indent=2) in user
