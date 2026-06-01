from ovf.context import Context
from ovf.nodes.base import Node, console
from ovf.providers.base import ImageProvider


class ImageNode(Node):
    name = "image"

    def __init__(self, provider: ImageProvider):
        self.provider = provider

    def _run(self, context: Context) -> Context:
        console.print(f"  Provider: [bold]{self.provider.name}[/bold]")
        images_dir = context.run_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        # Override provider output dir if it supports it
        if hasattr(self.provider, "output_dir"):
            self.provider.output_dir = images_dir  # type: ignore[attr-defined]

        for scene in context.scenes:
            console.print(f"  Generating image for scene {scene.index + 1}…")
            path = self.provider.generate(scene.prompt)
            scene.image_path = path
            context.images.append(path)
            console.print(f"    → {path}")

        return context
