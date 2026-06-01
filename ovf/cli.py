from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from ovf.config import load_config
from ovf.context import Context
from ovf.nodes.base import Node
from ovf.nodes.storyboard import StoryboardNode
from ovf.nodes.image import ImageNode
from ovf.nodes.video import VideoNode
from ovf.nodes.voice import VoiceNode
from ovf.nodes.render import RenderNode
from ovf.pipeline import Pipeline
from ovf.registry import get_image_provider, get_video_provider, get_audio_provider, list_providers
from ovf.storage import Storage

console = Console()

_NODE_NAMES = {"storyboard", "image", "video", "voice", "render"}


def _build_nodes(config) -> list[Node]:
    image_provider = None
    video_provider = None
    audio_provider = None

    if "image" in config.providers:
        pc = config.providers["image"]
        image_provider = get_image_provider(pc.provider, **pc.options)

    if "video" in config.providers:
        pc = config.providers["video"]
        video_provider = get_video_provider(pc.provider, **pc.options)

    if "audio" in config.providers:
        pc = config.providers["audio"]
        audio_provider = get_audio_provider(pc.provider, **pc.options)

    nodes: list[Node] = []
    for name in config.pipeline:
        if name == "storyboard":
            llm_cfg = config.providers.get("llm")
            nodes.append(StoryboardNode(
                num_scenes=config.num_scenes,
                llm_provider=llm_cfg.provider if llm_cfg else None,
                api_key=llm_cfg.options.get("api_key") if llm_cfg else None,
            ))
        elif name == "image":
            if image_provider is None:
                raise ValueError("Pipeline includes 'image' node but no image provider is configured")
            nodes.append(ImageNode(provider=image_provider))
        elif name == "video":
            if video_provider is None:
                raise ValueError("Pipeline includes 'video' node but no video provider is configured")
            nodes.append(VideoNode(provider=video_provider))
        elif name == "voice":
            if audio_provider is None:
                raise ValueError("Pipeline includes 'voice' node but no audio provider is configured")
            nodes.append(VoiceNode(provider=audio_provider))
        elif name == "render":
            nodes.append(RenderNode(output_path=config.output))
        else:
            raise ValueError(f"Unknown node '{name}'. Known nodes: {', '.join(sorted(_NODE_NAMES))}")
    return nodes


@click.group()
def main():
    pass


@main.command()
@click.argument("config_path", metavar="CONFIG", type=click.Path(exists=True, path_type=Path))
@click.option("--workspace", default=None, help="Override workspace directory")
@click.option("--output", default=None, help="Override output file path")
def run(config_path: Path, workspace: Optional[str], output: Optional[str]):
    """Run a video generation pipeline from a YAML config file."""
    config = load_config(config_path)
    if workspace:
        config.workspace = workspace
    if output:
        config.output = output

    storage = Storage(config.workspace)
    run_dir = storage.new_run()
    console.print(f"Run directory: [dim]{run_dir}[/dim]")

    context = Context(prompt=config.prompt, run_dir=run_dir)
    nodes = _build_nodes(config)
    pipeline = Pipeline(*nodes)
    pipeline.run(context)


@main.command("list-providers")
def list_providers_cmd():
    """List all installed providers."""
    providers = list_providers()
    for ptype, entries in providers.items():
        table = Table(title=f"{ptype} providers", show_header=True)
        table.add_column("name", style="bold cyan")
        table.add_column("module", style="dim")
        for name, module in sorted(entries.items()):
            table.add_row(name, module)
        console.print(table)
