import json
import os
import re
from typing import Optional

from ovf.context import Context, Scene
from ovf.nodes.base import Node, console
from ovf.style import Style


class StoryboardNode(Node):
    """Breaks the prompt into scenes and applies style to each scene prompt.

    Uses an LLM if a provider is configured, otherwise falls back to
    heuristic sentence splitting so the pipeline works with zero API keys.
    """

    name = "storyboard"

    def __init__(
        self,
        num_scenes: int = 3,
        llm_provider: Optional[str] = None,
        api_key: Optional[str] = None,
        style: Optional[Style] = None,
    ):
        self.num_scenes = num_scenes
        self.llm_provider = llm_provider
        self.api_key = api_key
        self.style = style

    def _run(self, context: Context) -> Context:
        if self.llm_provider == "openai":
            raw_scenes = self._openai(context.prompt)
        elif self.llm_provider == "anthropic":
            raw_scenes = self._anthropic(context.prompt)
        else:
            raw_scenes = self._heuristic(context.prompt, self.num_scenes)

        if self.style:
            console.print(f"  Style: [bold magenta]{self.style.name}[/bold magenta]")
            styled = [self.style.apply(s) for s in raw_scenes]
        else:
            styled = raw_scenes

        context.scenes = [Scene(index=i, prompt=p) for i, p in enumerate(styled)]
        for scene in context.scenes:
            console.print(f"  Scene {scene.index + 1}: {scene.prompt}")
        return context

    def _openai(self, prompt: str) -> list[str]:
        import requests
        key = self.api_key or os.environ.get("OPENAI_API_KEY", "")
        if not key:
            raise ValueError("StoryboardNode llm_provider=openai requires OPENAI_API_KEY")
        system = (
            "You are a video storyboard writer. "
            f"Split the user's prompt into exactly {self.num_scenes} short scene descriptions. "
            "Each scene should be a single vivid sentence suitable as a video generation prompt. "
            "Return a JSON array of strings, nothing else."
        )
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                "temperature": 0.7,
            },
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        return self._parse_json_scenes(raw, prompt)

    def _anthropic(self, prompt: str) -> list[str]:
        import requests
        key = self.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise ValueError("StoryboardNode llm_provider=anthropic requires ANTHROPIC_API_KEY")
        system = (
            "You are a video storyboard writer. "
            f"Split the user's prompt into exactly {self.num_scenes} short scene descriptions. "
            "Each scene should be a single vivid sentence suitable as a video generation prompt. "
            "Return a JSON array of strings, nothing else."
        )
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 512,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"].strip()
        return self._parse_json_scenes(raw, prompt)

    def _parse_json_scenes(self, raw: str, fallback_prompt: str) -> list[str]:
        raw = re.sub(r"^```[a-z]*\n?", "", raw).rstrip("`").strip()
        try:
            scenes = json.loads(raw)
            if isinstance(scenes, list) and all(isinstance(s, str) for s in scenes):
                return scenes[: self.num_scenes]
        except json.JSONDecodeError:
            pass
        console.print("  [yellow]LLM returned unexpected format, falling back to heuristic.[/yellow]")
        return self._heuristic(fallback_prompt, self.num_scenes)

    def _heuristic(self, prompt: str, n: int) -> list[str]:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", prompt) if s.strip()]
        if len(sentences) >= n:
            return sentences[:n]
        base = sentences[0] if sentences else prompt
        beats = ["establishing shot", "close-up detail", "wide cinematic shot"]
        while len(sentences) < n:
            beat = beats[(len(sentences) - 1) % len(beats)]
            sentences.append(f"{base}, {beat}")
        return sentences
