from ovf.context import Context
from ovf.nodes.base import Node, console
from ovf.providers.base import VideoProvider


class VideoNode(Node):
    name = "video"

    def __init__(self, provider: VideoProvider):
        self.provider = provider

    def _run(self, context: Context) -> Context:
        console.print(f"  Provider: [bold]{self.provider.name}[/bold]")
        videos_dir = context.run_dir / "videos"
        videos_dir.mkdir(parents=True, exist_ok=True)

        if hasattr(self.provider, "output_dir"):
            self.provider.output_dir = videos_dir  # type: ignore[attr-defined]

        for scene in context.scenes:
            console.print(f"  Generating video for scene {scene.index + 1}…")
            path = self.provider.generate(scene.prompt, image=scene.image_path)
            scene.video_path = path
            context.videos.append(path)
            console.print(f"    → {path}")

        return context
