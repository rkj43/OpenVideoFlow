import json
from unittest.mock import MagicMock, patch

import pytest

from ovf.context import Context
from ovf.nodes.storyboard import StoryboardNode
from ovf.storage import Storage


def _ctx(tmp_path, prompt="A dragon over Dublin"):
    run_dir = Storage(tmp_path).new_run()
    return Context(prompt=prompt, run_dir=run_dir)


def test_heuristic_single_sentence(tmp_path):
    ctx = _ctx(tmp_path, "A dragon flies over Dublin")
    ctx = StoryboardNode(num_scenes=3)._run(ctx)
    assert len(ctx.scenes) == 3
    assert "establishing shot" in ctx.scenes[1].prompt
    assert "close-up detail" in ctx.scenes[2].prompt


def test_heuristic_multi_sentence(tmp_path):
    ctx = _ctx(tmp_path, "The sun rises. A dragon appears. It flies away.")
    ctx = StoryboardNode(num_scenes=3)._run(ctx)
    assert len(ctx.scenes) == 3
    assert "sun rises" in ctx.scenes[0].prompt


def test_heuristic_truncates(tmp_path):
    ctx = _ctx(tmp_path, "One. Two. Three. Four. Five.")
    ctx = StoryboardNode(num_scenes=2)._run(ctx)
    assert len(ctx.scenes) == 2


def test_openai_llm(tmp_path):
    scenes = ["Scene one.", "Scene two.", "Scene three."]
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"choices": [{"message": {"content": json.dumps(scenes)}}]}
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.post", return_value=mock_resp) as mock_post:
        ctx = _ctx(tmp_path)
        node = StoryboardNode(num_scenes=3, llm_provider="openai", api_key="test-key")
        ctx = node._run(ctx)

    assert len(ctx.scenes) == 3
    assert ctx.scenes[0].prompt == "Scene one."
    call_kwargs = mock_post.call_args
    assert "openai.com" in call_kwargs[0][0]


def test_anthropic_llm(tmp_path):
    scenes = ["Vista uno.", "Vista dos.", "Vista tres."]
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"content": [{"text": json.dumps(scenes)}]}
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.post", return_value=mock_resp) as mock_post:
        ctx = _ctx(tmp_path)
        node = StoryboardNode(num_scenes=3, llm_provider="anthropic", api_key="test-key")
        ctx = node._run(ctx)

    assert len(ctx.scenes) == 3
    assert ctx.scenes[1].prompt == "Vista dos."
    call_kwargs = mock_post.call_args
    assert "anthropic.com" in call_kwargs[0][0]


def test_llm_bad_json_falls_back(tmp_path):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"choices": [{"message": {"content": "not valid json at all"}}]}
    mock_resp.raise_for_status = MagicMock()

    with patch("requests.post", return_value=mock_resp):
        ctx = _ctx(tmp_path, "A peaceful lake at sunrise.")
        node = StoryboardNode(num_scenes=2, llm_provider="openai", api_key="test-key")
        ctx = node._run(ctx)

    assert len(ctx.scenes) == 2
