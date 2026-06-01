import os
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import requests

from ovf.providers.base import VideoProvider

FAL_MODELS = {
    "wan-i2v":       "fal-ai/wan/v2.1/1.3b/image-to-video",
    "wan-t2v":       "fal-ai/wan/v2.1/1.3b/text-to-video",
    "hunyuan-video": "fal-ai/hunyuan-video",
    "ltx-video":     "fal-ai/ltx-video",
    "kling-v2":      "fal-ai/kling-video/v2/master/text-to-video",
    "minimax-video": "fal-ai/minimax/video-01",
    "luma-ray2":     "fal-ai/luma-dream-machine/ray-2-flash",
}


class FalVideoProvider(VideoProvider):
    """Runs video models on fal.ai — fast serverless inference, no local GPU."""

    name = "fal"

    def __init__(
        self,
        model: str = "wan-t2v",
        api_key: Optional[str] = None,
        output_dir: Optional[Path] = None,
        poll_interval: float = 2.0,
        extra_params: Optional[dict] = None,
    ):
        self.api_key = api_key or os.environ.get("FAL_KEY", "")
        if not self.api_key:
            raise ValueError("FalVideoProvider requires FAL_KEY env var or api_key argument")
        self.model = FAL_MODELS.get(model, model)
        self.output_dir = output_dir or Path("workspace/fal_outputs")
        self.poll_interval = poll_interval
        self.extra_params = extra_params or {}

    def _headers(self) -> dict:
        return {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_input(self, prompt: str, image: Optional[Path], style_params: dict) -> dict:
        inp: dict[str, Any] = {"prompt": prompt, **style_params, **self.extra_params}
        if image:
            import base64
            mime = "image/png" if image.suffix.lower() == ".png" else "image/jpeg"
            b64 = base64.b64encode(image.read_bytes()).decode()
            inp["image_url"] = f"data:{mime};base64,{b64}"
        return inp

    def _submit(self, inp: dict) -> str:
        resp = requests.post(
            f"https://queue.fal.run/{self.model}",
            headers=self._headers(),
            json=inp,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["request_id"]

    def _poll(self, request_id: str) -> dict:
        status_url = f"https://queue.fal.run/{self.model}/requests/{request_id}/status"
        while True:
            resp = requests.get(status_url, headers=self._headers(), timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if data["status"] == "COMPLETED":
                break
            if data["status"] == "FAILED":
                raise RuntimeError(f"fal.ai request failed: {data.get('error')}")
            time.sleep(self.poll_interval)

        result_url = f"https://queue.fal.run/{self.model}/requests/{request_id}"
        resp = requests.get(result_url, headers=self._headers(), timeout=15)
        resp.raise_for_status()
        return resp.json()

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
        request_id = self._submit(inp)
        result = self._poll(request_id)

        # fal returns video under result.video.url or result[0].url depending on model
        video = result.get("video") or (result.get("videos") or [{}])[0]
        url = video.get("url") if isinstance(video, dict) else video
        if not url:
            raise RuntimeError(f"No video URL in fal.ai response: {result}")
        return self._download(url, self.output_dir)
