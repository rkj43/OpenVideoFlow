import textwrap
from pathlib import Path

import pytest

from ovf.config import load_config


def write_yaml(tmp_path, content: str) -> Path:
    p = tmp_path / "config.yaml"
    p.write_text(textwrap.dedent(content))
    return p


def test_basic_config(tmp_path):
    p = write_yaml(tmp_path, """
        input:
          prompt: "A dragon over Dublin"
        pipeline:
          - storyboard
          - image
          - video
          - render
        providers:
          image:
            provider: comfyui
            workflow: workflows/flux.json
          video:
            provider: comfyui
            workflow: workflows/wan.json
    """)
    cfg = load_config(p)
    assert cfg.prompt == "A dragon over Dublin"
    assert cfg.pipeline == ["storyboard", "image", "video", "render"]
    assert cfg.providers["image"].provider == "comfyui"
    assert cfg.providers["image"].options["workflow"] == "workflows/flux.json"
    assert cfg.providers["video"].provider == "comfyui"


def test_defaults(tmp_path):
    p = write_yaml(tmp_path, """
        input:
          prompt: "test"
    """)
    cfg = load_config(p)
    assert cfg.workspace == "workspace"
    assert cfg.output == "output.mp4"
    assert cfg.pipeline == ["storyboard", "image", "video", "render"]
