import re

from ovf.context import Context, Scene
from ovf.nodes.base import Node, console


class StoryboardNode(Node):
    """Breaks the prompt into scenes. Uses simple heuristic splitting in V1."""

    name = "storyboard"

    def __init__(self, num_scenes: int = 3):
        self.num_scenes = num_scenes

    def _run(self, context: Context) -> Context:
        scenes = self._split(context.prompt, self.num_scenes)
        context.scenes = [Scene(index=i, prompt=p) for i, p in enumerate(scenes)]
        for scene in context.scenes:
            console.print(f"  Scene {scene.index + 1}: {scene.prompt}")
        return context

    def _split(self, prompt: str, n: int) -> list[str]:
        # Split on sentence boundaries first; pad or truncate to n scenes.
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", prompt) if s.strip()]
        if len(sentences) >= n:
            return sentences[:n]

        # Pad by appending continuation prompts derived from the original.
        base = sentences[0] if sentences else prompt
        beats = ["establishing shot", "close-up detail", "wide cinematic shot"]
        while len(sentences) < n:
            beat = beats[(len(sentences) - 1) % len(beats)]
            sentences.append(f"{base}, {beat}")
        return sentences
