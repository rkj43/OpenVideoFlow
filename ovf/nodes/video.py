from typing import Optional

from ovf.context import Context
from ovf.nodes.base import Node, console
from ovf.providers.base import VideoProvider
from ovf.style import Style


class VideoNode(Node):
    name = "video"

    def __init__(self, provider: VideoProvider, style: Optional[Style] = None):
        self.provider = provider
        self.style = style

    def _run(self, context: Context) -> Context:
        console.print(f"  Provider: [bold]{self.provider.name}[/bold]")
        videos_dir = context.run_dir / "videos"
        videos_dir.mkdir(parents=True, exist_ok=True)

        if hasattr(self.provider, "output_dir"):
            self.provider.output_dir = videos_dir  # type: ignore[attr-defined]

        style_params = self.style.provider_params if self.style else {}

        for scene in context.scenes:
            console.print(f"  Generating video for scene {scene.index + 1}…")
            path = self.provider.generate(scene.prompt, image=scene.image_path, style_params=style_params)
            scene.video_path = path
            context.videos.append(path)
            console.print(f"    → {path}")

        return context
