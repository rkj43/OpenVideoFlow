from datetime import datetime
from pathlib import Path


class Storage:
    def __init__(self, workspace: str | Path = "workspace"):
        self.workspace = Path(workspace)

    def new_run(self) -> Path:
        run_id = datetime.now().strftime("run_%Y%m%d_%H%M%S")
        run_dir = self.workspace / "runs" / run_id
        for subdir in ("images", "videos", "audio", "metadata", "logs"):
            (run_dir / subdir).mkdir(parents=True, exist_ok=True)
        return run_dir

    def images_dir(self, run_dir: Path) -> Path:
        return run_dir / "images"

    def videos_dir(self, run_dir: Path) -> Path:
        return run_dir / "videos"

    def audio_dir(self, run_dir: Path) -> Path:
        return run_dir / "audio"

    def logs_dir(self, run_dir: Path) -> Path:
        return run_dir / "logs"
