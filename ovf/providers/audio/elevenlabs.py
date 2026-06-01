import os
import uuid
from pathlib import Path
from typing import Any, Optional

import requests

from ovf.providers.base import AudioProvider


class ElevenLabsProvider(AudioProvider):
    """Text-to-speech via ElevenLabs API."""

    name = "elevenlabs"

    def __init__(
        self,
        api_key: Optional[str] = None,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # default: Rachel
        model_id: str = "eleven_multilingual_v2",
        output_dir: Optional[Path] = None,
    ):
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")
        if not self.api_key:
            raise ValueError("ElevenLabsProvider requires ELEVENLABS_API_KEY env var or api_key argument")
        self.voice_id = voice_id
        self.model_id = model_id
        self.output_dir = output_dir or Path("workspace/audio")

    def generate(self, prompt: str, **kwargs: Any) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {"xi-api-key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "text": prompt,
            "model_id": self.model_id,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        dest = self.output_dir / f"{uuid.uuid4()}.mp3"
        dest.write_bytes(resp.content)
        return dest
