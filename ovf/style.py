from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

_BUILTIN_DIR = Path(__file__).parent / "styles"


@dataclass
class Style:
    name: str
    prompt_prefix: str = ""
    prompt_suffix: str = ""
    negative_prompt: str = ""
    provider_params: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def apply(self, prompt: str) -> str:
        parts = []
        if self.prompt_prefix:
            parts.append(self.prompt_prefix.rstrip(",").rstrip() + ",")
        parts.append(prompt)
        if self.prompt_suffix:
            parts.append("," + self.prompt_suffix.lstrip(","))
        return " ".join(parts)


def load_style(name_or_path: str) -> Style:
    path = Path(name_or_path)

    # treat as file path if it has a slash or .yaml extension
    if path.suffix == ".yaml" or "/" in name_or_path:
        if not path.exists():
            raise FileNotFoundError(f"Style file not found: {path}")
        return _from_file(path)

    # built-in preset
    builtin = _BUILTIN_DIR / f"{name_or_path}.yaml"
    if builtin.exists():
        return _from_file(builtin)

    available = [p.stem for p in _BUILTIN_DIR.glob("*.yaml")]
    raise ValueError(f"Unknown style '{name_or_path}'. Built-in styles: {', '.join(sorted(available))}")


def _from_file(path: Path) -> Style:
    with open(path) as f:
        raw = yaml.safe_load(f)
    return Style(
        name=raw.get("name", path.stem),
        prompt_prefix=raw.get("prompt_prefix", ""),
        prompt_suffix=raw.get("prompt_suffix", ""),
        negative_prompt=raw.get("negative_prompt", ""),
        provider_params=raw.get("provider_params", {}),
        description=raw.get("description", ""),
    )
