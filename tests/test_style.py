import textwrap
from pathlib import Path

import pytest

from ovf.style import Style, load_style


def test_load_builtin_news_report():
    s = load_style("news_report")
    assert s.name == "news_report"
    assert "broadcast" in s.prompt_prefix
    assert s.negative_prompt


def test_load_builtin_cinematic():
    s = load_style("cinematic")
    assert "cinematic" in s.prompt_prefix


def test_load_all_builtins():
    for name in ("news_report", "cinematic", "documentary", "anime", "commercial", "music_video"):
        s = load_style(name)
        assert s.name
        assert s.description


def test_unknown_style_raises():
    with pytest.raises(ValueError, match="Unknown style"):
        load_style("does_not_exist_xyz")


def test_load_custom_file(tmp_path):
    p = tmp_path / "noir.yaml"
    p.write_text(textwrap.dedent("""
        name: noir
        description: Dark noir style
        prompt_prefix: "dark noir film,"
        prompt_suffix: ", black and white, shadows"
        negative_prompt: "bright, colorful"
        provider_params:
          cfg_scale: 9.0
    """))
    s = load_style(str(p))
    assert s.name == "noir"
    assert s.provider_params["cfg_scale"] == 9.0


def test_style_apply():
    s = Style(name="test", prompt_prefix="cinematic,", prompt_suffix=", 4K")
    result = s.apply("a dragon flies")
    assert result.startswith("cinematic,")
    assert "a dragon flies" in result
    assert result.endswith(", 4K")


def test_style_apply_empty_affixes():
    s = Style(name="plain")
    assert s.apply("a dragon flies") == "a dragon flies"


def test_storyboard_applies_style(tmp_path):
    from ovf.context import Context
    from ovf.nodes.storyboard import StoryboardNode
    from ovf.storage import Storage

    run_dir = Storage(tmp_path).new_run()
    ctx = Context(prompt="A breaking news story.", run_dir=run_dir)
    style = load_style("news_report")
    node = StoryboardNode(num_scenes=1, style=style)
    ctx = node._run(ctx)
    assert "broadcast" in ctx.scenes[0].prompt
