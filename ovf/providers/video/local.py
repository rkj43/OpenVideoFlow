from pathlib import Path
from typing import Any, Optional

from ovf.providers.base import VideoProvider


class LocalVideoProvider(VideoProvider):
    """Pass-through provider — returns a pre-existing video file path unchanged."""

    name = "local"

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def generate(self, prompt: str, image: Optional[Path] = None, **kwargs: Any) -> Path:
        if not self.path.exists():
            raise FileNotFoundError(f"LocalVideoProvider: file not found: {self.path}")
        return self.path
