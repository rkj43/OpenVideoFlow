import shutil
from pathlib import Path

from ovf.context import Context
from ovf.nodes.base import Node, console


class RenderNode(Node):
    """Assembles scene videos into a final output file.

    V1: copies/concatenates using ffmpeg if available, otherwise just copies
    the first video as a placeholder so the pipeline always produces output.
    """

    name = "render"

    def __init__(self, output_path: str | Path = "output.mp4"):
        self.output_path = Path(output_path)

    def _run(self, context: Context) -> Context:
        if not context.videos:
            raise RuntimeError("RenderNode: no videos in context to render")

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        if self._ffmpeg_available() and len(context.videos) > 1:
            self._concat_ffmpeg(context.videos, self.output_path)
        else:
            shutil.copy2(context.videos[0], self.output_path)
            if len(context.videos) > 1:
                console.print(
                    f"  [yellow]ffmpeg not found — copied scene 1 only. "
                    f"Install ffmpeg to concatenate all {len(context.videos)} scenes.[/yellow]"
                )

        context.output_path = self.output_path
        console.print(f"  Output: [bold green]{self.output_path}[/bold green]")
        return context

    def _ffmpeg_available(self) -> bool:
        import shutil as sh
        return sh.which("ffmpeg") is not None

    def _concat_ffmpeg(self, videos: list[Path], output: Path) -> None:
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            for v in videos:
                f.write(f"file '{v.resolve()}'\n")
            list_path = f.name

        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", str(output)],
            check=True,
            capture_output=True,
        )
        Path(list_path).unlink(missing_ok=True)
