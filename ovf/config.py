from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ProviderConfig:
    provider: str
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class OVFConfig:
    prompt: str
    pipeline: list[str]
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    workspace: str = "workspace"
    output: str = "output.mp4"
    num_scenes: int = 3


def load_config(path: str | Path) -> OVFConfig:
    with open(path) as f:
        raw = yaml.safe_load(f)

    prompt = raw.get("input", {}).get("prompt", "")
    pipeline = raw.get("pipeline", ["storyboard", "image", "video", "render"])
    workspace = raw.get("workspace", "workspace")
    output = raw.get("output", "output.mp4")
    num_scenes = raw.get("num_scenes", 3)

    providers: dict[str, ProviderConfig] = {}
    for key, val in raw.get("providers", {}).items():
        if isinstance(val, dict):
            val = dict(val)
            name = val.pop("provider")
            providers[key] = ProviderConfig(provider=name, options=val)
        else:
            providers[key] = ProviderConfig(provider=str(val))

    return OVFConfig(
        prompt=prompt,
        pipeline=pipeline,
        providers=providers,
        workspace=workspace,
        output=output,
        num_scenes=num_scenes,
    )
