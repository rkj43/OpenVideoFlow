from pathlib import Path
from typing import Any

from ovf.providers.base import AudioProvider


class LocalAudioProvider(AudioProvider):
    """Pass-through provider — returns a pre-existing audio file path unchanged."""

    name = "local"

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def generate(self, prompt: str, **kwargs: Any) -> Path:
        if not self.path.exists():
            raise FileNotFoundError(f"LocalAudioProvider: file not found: {self.path}")
        return self.path
