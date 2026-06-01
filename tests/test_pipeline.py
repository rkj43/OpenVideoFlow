from pathlib import Path
import pytest

from ovf.context import Context, Scene
from ovf.nodes.storyboard import StoryboardNode
from ovf.nodes.image import ImageNode
from ovf.nodes.video import VideoNode
from ovf.pipeline import Pipeline
from ovf.providers.base import ImageProvider, VideoProvider
from ovf.result import TaskResult
from ovf.storage import Storage


class _StubImageProvider(ImageProvider):
    name = "stub"

    def generate(self, prompt, **kwargs):
        return Path("/tmp/stub_image.png")


class _StubVideoProvider(VideoProvider):
    name = "stub"

    def generate(self, prompt, image=None, **kwargs):
        return Path("/tmp/stub_video.mp4")


def _make_context(tmp_path) -> Context:
    storage = Storage(tmp_path)
    run_dir = storage.new_run()
    return Context(prompt="A dragon over Dublin", run_dir=run_dir)


def test_storyboard_splits_into_scenes(tmp_path):
    ctx = _make_context(tmp_path)
    node = StoryboardNode(num_scenes=3)
    ctx = node.run(ctx)
    assert len(ctx.scenes) == 3
    for i, scene in enumerate(ctx.scenes):
        assert scene.index == i
        assert scene.prompt


def test_storyboard_multi_sentence(tmp_path):
    ctx = _make_context(tmp_path)
    ctx.prompt = "The sun rises. A dragon appears. It flies away."
    node = StoryboardNode(num_scenes=3)
    ctx = node.run(ctx)
    assert len(ctx.scenes) == 3
    assert "sun rises" in ctx.scenes[0].prompt


def test_image_node_populates_context(tmp_path):
    ctx = _make_context(tmp_path)
    ctx.scenes = [Scene(0, "scene one"), Scene(1, "scene two")]
    node = ImageNode(provider=_StubImageProvider())
    ctx = node.run(ctx)
    assert len(ctx.images) == 2
    assert all(p == Path("/tmp/stub_image.png") for p in ctx.images)
    assert ctx.scenes[0].image_path == Path("/tmp/stub_image.png")


def test_video_node_populates_context(tmp_path):
    ctx = _make_context(tmp_path)
    ctx.scenes = [Scene(0, "scene one", image_path=Path("/tmp/img.png"))]
    node = VideoNode(provider=_StubVideoProvider())
    ctx = node.run(ctx)
    assert len(ctx.videos) == 1
    assert ctx.scenes[0].video_path == Path("/tmp/stub_video.mp4")


def test_pipeline_runs_sequentially(tmp_path):
    ctx = _make_context(tmp_path)
    pipeline = Pipeline(
        StoryboardNode(num_scenes=2),
        ImageNode(provider=_StubImageProvider()),
        VideoNode(provider=_StubVideoProvider()),
    )
    result_ctx = pipeline.run(ctx)
    assert len(result_ctx.scenes) == 2
    assert len(result_ctx.images) == 2
    assert len(result_ctx.videos) == 2


def test_task_result_ok_property():
    r = TaskResult(status="success", output="x", duration=1.0)
    assert r.ok
    r2 = TaskResult(status="error", output=None, error="boom", duration=0.1)
    assert not r2.ok


def test_storage_creates_run_dirs(tmp_path):
    storage = Storage(tmp_path)
    run_dir = storage.new_run()
    assert (run_dir / "images").is_dir()
    assert (run_dir / "videos").is_dir()
    assert (run_dir / "audio").is_dir()
    assert (run_dir / "logs").is_dir()
