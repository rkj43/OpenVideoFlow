import json
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import requests

from ovf.providers.base import VideoProvider


class ComfyUIVideoProvider(VideoProvider):
    """Executes a ComfyUI workflow JSON to generate video via the ComfyUI API."""

    name = "comfyui"

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8188,
        workflow: Optional[str | Path] = None,
        prompt_node_id: str = "6",
        image_node_id: Optional[str] = None,
        output_dir: Optional[Path] = None,
        poll_interval: float = 2.0,
    ):
        self.base_url = f"http://{host}:{port}"
        self.workflow_path = Path(workflow) if workflow else None
        self.prompt_node_id = prompt_node_id
        self.image_node_id = image_node_id
        self.output_dir = output_dir or Path("workspace/comfyui_outputs")
        self.poll_interval = poll_interval
        self.client_id = str(uuid.uuid4())

    def _load_workflow(self) -> dict:
        if self.workflow_path is None:
            raise ValueError("ComfyUIVideoProvider requires a workflow JSON path")
        with open(self.workflow_path) as f:
            return json.load(f)

    def _inject(self, workflow: dict, prompt: str, image: Optional[Path]) -> dict:
        wf = json.loads(json.dumps(workflow))  # deep copy

        if self.prompt_node_id in wf:
            node = wf[self.prompt_node_id]
            inputs = node.get("inputs", {})
            # CLIPTextEncode uses "text"; fallback to common alternatives
            for key in ("text", "prompt", "positive"):
                if key in inputs:
                    inputs[key] = prompt
                    break

        if image and self.image_node_id and self.image_node_id in wf:
            node = wf[self.image_node_id]
            inputs = node.get("inputs", {})
            for key in ("image", "image_path", "init_image"):
                if key in inputs:
                    inputs[key] = str(image)
                    break

        return wf

    def _queue(self, workflow: dict) -> str:
        payload = {"prompt": workflow, "client_id": self.client_id}
        resp = requests.post(f"{self.base_url}/prompt", json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["prompt_id"]

    def _poll(self, prompt_id: str) -> dict:
        while True:
            resp = requests.get(f"{self.base_url}/history/{prompt_id}", timeout=10)
            resp.raise_for_status()
            history = resp.json()
            if prompt_id in history:
                return history[prompt_id]
            time.sleep(self.poll_interval)

    def _download(self, result: dict, dest_dir: Path) -> Path:
        dest_dir.mkdir(parents=True, exist_ok=True)
        outputs = result.get("outputs", {})
        for node_output in outputs.values():
            for file_list in node_output.values():
                if not isinstance(file_list, list):
                    continue
                for item in file_list:
                    if not isinstance(item, dict):
                        continue
                    filename = item.get("filename")
                    subfolder = item.get("subfolder", "")
                    file_type = item.get("type", "output")
                    if not filename:
                        continue
                    url = f"{self.base_url}/view?filename={filename}&subfolder={subfolder}&type={file_type}"
                    dest = dest_dir / filename
                    with requests.get(url, stream=True, timeout=60) as r:
                        r.raise_for_status()
                        with open(dest, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                    return dest
        raise RuntimeError("No output files found in ComfyUI history result")

    def generate(self, prompt: str, image: Optional[Path] = None, **kwargs: Any) -> Path:
        workflow = self._load_workflow()
        workflow = self._inject(workflow, prompt, image)
        prompt_id = self._queue(workflow)
        result = self._poll(prompt_id)
        return self._download(result, self.output_dir)
