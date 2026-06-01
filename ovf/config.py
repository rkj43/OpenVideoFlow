from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

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


def load_config(path: str | Path) -> OVFConfig:
    with open(path) as f:
        raw = yaml.safe_load(f)

    prompt = raw.get("input", {}).get("prompt", "")
    pipeline = raw.get("pipeline", ["storyboard", "image", "video", "render"])
    workspace = raw.get("workspace", "workspace")
    output = raw.get("output", "output.mp4")

    providers: dict[str, ProviderConfig] = {}
    for key, val in raw.get("providers", {}).items():
        if isinstance(val, dict):
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
    )
