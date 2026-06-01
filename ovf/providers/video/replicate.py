import os
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import requests

from ovf.providers.base import VideoProvider

# Curated model aliases — users can also pass any replicate model string directly
REPLICATE_MODELS = {
    "wan-i2v":        "wavespeedai/wan-2.1-i2v-480p",
    "wan-t2v":        "wavespeedai/wan-2.1-t2v-720p",
    "hunyuan-video":  "tencent/hunyuan-video",
    "ltx-video":      "lightricks/ltx-video",
    "cogvideox-5b":   "chenxwh/cogvideox-5b",
    "minimax-video":  "minimax/video-01",
    "luma-ray2":      "luma/ray2-flash",
}


class ReplicateVideoProvider(VideoProvider):
    """Runs any video model on Replicate — no local GPU required."""

    name = "replicate"

    def __init__(
        self,
        model: str = "wan-t2v",
        api_key: Optional[str] = None,
        output_dir: Optional[Path] = None,
        poll_interval: float = 3.0,
        extra_params: Optional[dict] = None,
    ):
        self.api_key = api_key or os.environ.get("REPLICATE_API_TOKEN", "")
        if not self.api_key:
            raise ValueError("ReplicateVideoProvider requires REPLICATE_API_TOKEN env var or api_key argument")
        # resolve alias or use raw model string (owner/name or owner/name:version)
        self.model = REPLICATE_MODELS.get(model, model)
        self.output_dir = output_dir or Path("workspace/replicate_outputs")
        self.poll_interval = poll_interval
        self.extra_params = extra_params or {}

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "wait",
        }

    def _build_input(self, prompt: str, image: Optional[Path], style_params: dict) -> dict:
        inp: dict[str, Any] = {"prompt": prompt, **style_params, **self.extra_params}
        if image:
            # encode as data URI so Replicate accepts a local file
            import base64
            mime = "image/png" if image.suffix.lower() == ".png" else "image/jpeg"
            b64 = base64.b64encode(image.read_bytes()).decode()
            inp["image"] = f"data:{mime};base64,{b64}"
        return inp

    def _run_prediction(self, inp: dict) -> dict:
        # use predictions/create then poll, or use the synchronous wait endpoint
        resp = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers=self._headers(),
            json={"version": self._resolve_version(), "input": inp},
            timeout=30,
        )
        resp.raise_for_status()
        prediction = resp.json()

        while prediction["status"] not in ("succeeded", "failed", "canceled"):
            time.sleep(self.poll_interval)
            r = requests.get(prediction["urls"]["get"], headers=self._headers(), timeout=15)
            r.raise_for_status()
            prediction = r.json()

        if prediction["status"] != "succeeded":
            raise RuntimeError(f"Replicate prediction failed: {prediction.get('error')}")
        return prediction

    def _resolve_version(self) -> str:
        # if model already contains a version hash (:) return as-is
        if ":" in self.model:
            return self.model.split(":")[1]
        # fetch latest version from the API
        owner, name = self.model.split("/")
        resp = requests.get(
            f"https://api.replicate.com/v1/models/{owner}/{name}",
            headers=self._headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["latest_version"]["id"]

    def _download(self, url: str, dest_dir: Path) -> Path:
        dest_dir.mkdir(parents=True, exist_ok=True)
        ext = url.split("?")[0].rsplit(".", 1)[-1] or "mp4"
        dest = dest_dir / f"{uuid.uuid4()}.{ext}"
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return dest

    def generate(self, prompt: str, image: Optional[Path] = None, **kwargs: Any) -> Path:
        style_params = kwargs.get("style_params", {})
        inp = self._build_input(prompt, image, style_params)
        prediction = self._run_prediction(inp)

        output = prediction["output"]
        # output is either a URL string or a list; grab the first video URL
        url = output[0] if isinstance(output, list) else output
        return self._download(url, self.output_dir)
