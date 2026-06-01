from pathlib import Path
from typing import Any, Optional


class VideoProvider:
    name: str = "base"

    def generate(self, prompt: str, image: Optional[Path] = None, **kwargs: Any) -> Path:
        raise NotImplementedError(f"{self.__class__.__name__}.generate() is not implemented")


class ImageProvider:
    name: str = "base"

    def generate(self, prompt: str, **kwargs: Any) -> Path:
        raise NotImplementedError(f"{self.__class__.__name__}.generate() is not implemented")


class AudioProvider:
    name: str = "base"

    def generate(self, prompt: str, **kwargs: Any) -> Path:
        raise NotImplementedError(f"{self.__class__.__name__}.generate() is not implemented")
