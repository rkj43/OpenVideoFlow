from pathlib import Path

import pytest

from ovf.context import Context, Scene
from ovf.nodes.voice import VoiceNode
from ovf.providers.base import AudioProvider
from ovf.storage import Storage


class _StubAudioProvider(AudioProvider):
    name = "stub"

    def generate(self, prompt, **kwargs):
        return Path("/tmp/stub_audio.mp3")


def _ctx(tmp_path):
    run_dir = Storage(tmp_path).new_run()
    ctx = Context(prompt="test", run_dir=run_dir)
    ctx.scenes = [Scene(0, "scene one"), Scene(1, "scene two")]
    return ctx


def test_voice_node_populates_audio(tmp_path):
    ctx = _ctx(tmp_path)
    node = VoiceNode(provider=_StubAudioProvider())
    ctx = node.run(ctx)
    assert len(ctx.audio) == 2
    assert all(p == Path("/tmp/stub_audio.mp3") for p in ctx.audio)


def test_voice_node_creates_audio_dir(tmp_path):
    ctx = _ctx(tmp_path)
    node = VoiceNode(provider=_StubAudioProvider())
    node.run(ctx)
    assert (ctx.run_dir / "audio").is_dir()
