from pathlib import Path
from typing import Any

from ovf.providers.base import ImageProvider


class LocalImageProvider(ImageProvider):
    """Pass-through provider — returns a pre-existing image file path unchanged."""

    name = "local"

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def generate(self, prompt: str, **kwargs: Any) -> Path:
        if not self.path.exists():
            raise FileNotFoundError(f"LocalImageProvider: file not found: {self.path}")
        return self.path
