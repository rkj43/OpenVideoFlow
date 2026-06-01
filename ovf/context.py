from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class Scene:
    index: int
    prompt: str
    image_path: Optional[Path] = None
    video_path: Optional[Path] = None


@dataclass
class Context:
    prompt: str
    run_dir: Path
    scenes: list[Scene] = field(default_factory=list)
    images: list[Path] = field(default_factory=list)
    videos: list[Path] = field(default_factory=list)
    audio: list[Path] = field(default_factory=list)
    output_path: Optional[Path] = None
    metadata: dict[str, Any] = field(default_factory=dict)
