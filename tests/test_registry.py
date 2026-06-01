import pytest

from ovf.registry import get_image_provider, get_video_provider
from ovf.providers.video.comfyui import ComfyUIVideoProvider
from ovf.providers.video.local import LocalVideoProvider
from ovf.providers.image.comfyui import ComfyUIImageProvider
from ovf.providers.image.local import LocalImageProvider


def test_get_video_provider_comfyui():
    p = get_video_provider("comfyui")
    assert isinstance(p, ComfyUIVideoProvider)


def test_get_video_provider_local(tmp_path):
    f = tmp_path / "v.mp4"
    f.touch()
    p = get_video_provider("local", path=str(f))
    assert isinstance(p, LocalVideoProvider)


def test_get_image_provider_comfyui():
    p = get_image_provider("comfyui")
    assert isinstance(p, ComfyUIImageProvider)


def test_get_image_provider_local(tmp_path):
    f = tmp_path / "img.png"
    f.touch()
    p = get_image_provider("local", path=str(f))
    assert isinstance(p, LocalImageProvider)


def test_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown video provider"):
        get_video_provider("nonexistent_provider_xyz")
