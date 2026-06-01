from importlib.metadata import entry_points
from typing import Any, Type

from ovf.providers.base import AudioProvider, ImageProvider, VideoProvider
from ovf.providers.video.comfyui import ComfyUIVideoProvider
from ovf.providers.video.local import LocalVideoProvider
from ovf.providers.video.replicate import ReplicateVideoProvider
from ovf.providers.video.fal import FalVideoProvider
from ovf.providers.image.comfyui import ComfyUIImageProvider
from ovf.providers.image.local import LocalImageProvider
from ovf.providers.audio.local import LocalAudioProvider
from ovf.providers.audio.elevenlabs import ElevenLabsProvider

_BUILTIN_VIDEO: dict[str, Type[VideoProvider]] = {
    "comfyui":   ComfyUIVideoProvider,
    "replicate": ReplicateVideoProvider,
    "fal":       FalVideoProvider,
    "local":     LocalVideoProvider,
}

_BUILTIN_IMAGE: dict[str, Type[ImageProvider]] = {
    "comfyui": ComfyUIImageProvider,
    "local":   LocalImageProvider,
}

_BUILTIN_AUDIO: dict[str, Type[AudioProvider]] = {
    "local":       LocalAudioProvider,
    "elevenlabs":  ElevenLabsProvider,
}


def _load_plugins(group: str) -> dict[str, type]:
    plugins: dict[str, type] = {}
    for ep in entry_points(group=group):
        plugins[ep.name] = ep.load()
    return plugins


def get_video_provider(name: str, **options: Any) -> VideoProvider:
    registry = {**_load_plugins("ovf.providers.video"), **_BUILTIN_VIDEO}
    cls = registry.get(name)
    if cls is None:
        available = ", ".join(sorted(registry))
        raise ValueError(f"Unknown video provider '{name}'. Available: {available}")
    return cls(**options)


def get_image_provider(name: str, **options: Any) -> ImageProvider:
    registry = {**_load_plugins("ovf.providers.image"), **_BUILTIN_IMAGE}
    cls = registry.get(name)
    if cls is None:
        available = ", ".join(sorted(registry))
        raise ValueError(f"Unknown image provider '{name}'. Available: {available}")
    return cls(**options)


def get_audio_provider(name: str, **options: Any) -> AudioProvider:
    registry = {**_load_plugins("ovf.providers.audio"), **_BUILTIN_AUDIO}
    cls = registry.get(name)
    if cls is None:
        available = ", ".join(sorted(registry))
        raise ValueError(f"Unknown audio provider '{name}'. Available: {available}")
    return cls(**options)


def list_providers() -> dict[str, dict[str, str]]:
    return {
        "video": {k: v.__module__ for k, v in {**_load_plugins("ovf.providers.video"), **_BUILTIN_VIDEO}.items()},
        "image": {k: v.__module__ for k, v in {**_load_plugins("ovf.providers.image"), **_BUILTIN_IMAGE}.items()},
        "audio": {k: v.__module__ for k, v in {**_load_plugins("ovf.providers.audio"), **_BUILTIN_AUDIO}.items()},
    }
