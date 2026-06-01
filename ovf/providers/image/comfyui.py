import json
import time
import uuid
from pathlib import Path
from typing import Any, Optional

import requests

from ovf.providers.base import ImageProvider


class ComfyUIImageProvider(ImageProvider):
    """Executes a ComfyUI workflow JSON to generate images via the ComfyUI API."""

    name = "comfyui"

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8188,
        workflow: Optional[str | Path] = None,
        prompt_node_id: str = "6",
        output_dir: Optional[Path] = None,
        poll_interval: float = 2.0,
    ):
        self.base_url = f"http://{host}:{port}"
        self.workflow_path = Path(workflow) if workflow else None
        self.prompt_node_id = prompt_node_id
        self.output_dir = output_dir or Path("workspace/comfyui_outputs")
        self.poll_interval = poll_interval
        self.client_id = str(uuid.uuid4())

    def _load_workflow(self) -> dict:
        if self.workflow_path is None:
            raise ValueError("ComfyUIImageProvider requires a workflow JSON path")
        with open(self.workflow_path) as f:
            return json.load(f)

    def _inject_prompt(self, workflow: dict, prompt: str) -> dict:
        wf = json.loads(json.dumps(workflow))
        if self.prompt_node_id in wf:
            inputs = wf[self.prompt_node_id].get("inputs", {})
            for key in ("text", "prompt", "positive"):
                if key in inputs:
                    inputs[key] = prompt
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
        for node_output in result.get("outputs", {}).values():
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

    def generate(self, prompt: str, **kwargs: Any) -> Path:
        workflow = self._load_workflow()
        workflow = self._inject_prompt(workflow, prompt)
        prompt_id = self._queue(workflow)
        result = self._poll(prompt_id)
        return self._download(result, self.output_dir)
