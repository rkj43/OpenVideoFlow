from ovf.context import Context
from ovf.nodes.base import Node, console
from ovf.providers.base import AudioProvider


class VoiceNode(Node):
    name = "voice"

    def __init__(self, provider: AudioProvider):
        self.provider = provider

    def _run(self, context: Context) -> Context:
        console.print(f"  Provider: [bold]{self.provider.name}[/bold]")
        audio_dir = context.run_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        if hasattr(self.provider, "output_dir"):
            self.provider.output_dir = audio_dir  # type: ignore[attr-defined]

        for scene in context.scenes:
            console.print(f"  Generating voice for scene {scene.index + 1}…")
            path = self.provider.generate(scene.prompt)
            context.audio.append(path)
            console.print(f"    → {path}")

        return context
