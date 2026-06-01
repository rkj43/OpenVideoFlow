# OpenVideoFlow

Open-source workflow orchestration for AI video generation.

Swap models and providers without changing pipeline logic.

## Quick start

```bash
pip install openvideoflow
ovf run examples/dragon_comfyui.yaml
```

## How it works

A **pipeline** is a sequence of **nodes**. Each node reads from and writes to a shared **context**.

```python
from ovf import Pipeline, StoryboardNode, ImageNode, VideoNode, RenderNode
from ovf.providers.video.comfyui import ComfyUIVideoProvider
from ovf.providers.image.comfyui import ComfyUIImageProvider
from ovf.context import Context
from ovf.storage import Storage

image_provider = ComfyUIImageProvider(workflow="workflows/flux_t2i.json")
video_provider = ComfyUIVideoProvider(workflow="workflows/wan_i2v.json")

pipeline = Pipeline(
    StoryboardNode(num_scenes=3),
    ImageNode(provider=image_provider),
    VideoNode(provider=video_provider),
    RenderNode(output_path="output.mp4"),
)

storage = Storage()
run_dir = storage.new_run()
context = Context(prompt="A dragon flying over Dublin", run_dir=run_dir)
pipeline.run(context)
```

## YAML config

```yaml
input:
  prompt: "A dragon flying over Dublin at golden hour"

pipeline:
  - storyboard
  - image
  - video
  - render

providers:
  image:
    provider: comfyui
    host: "127.0.0.1"
    port: 8188
    workflow: "workflows/flux_t2i.json"
    prompt_node_id: "6"

  video:
    provider: comfyui
    host: "127.0.0.1"
    port: 8188
    workflow: "workflows/wan_i2v.json"
    prompt_node_id: "6"
    image_node_id: "12"

output: "output.mp4"
```

```bash
ovf run config.yaml
```

## Providers

### V1 (built-in)

| Type  | Provider    | Description                                      |
|-------|-------------|--------------------------------------------------|
| video | `comfyui`   | Any ComfyUI workflow — Wan, HunyuanVideo, LTX, CogVideoX, AnimateDiff, … |
| video | `local`     | Pass-through for a pre-existing file             |
| image | `comfyui`   | Any ComfyUI workflow — Flux, SDXL, …            |
| image | `local`     | Pass-through for a pre-existing file             |
| audio | `local`     | Pass-through for a pre-existing file             |

### Adding a provider (plugin)

```python
# ovf_kling/provider.py
from ovf.providers.base import VideoProvider

class KlingProvider(VideoProvider):
    name = "kling"

    def generate(self, prompt, image=None, **kwargs):
        ...
```

```toml
# pyproject.toml
[project.entry-points."ovf.providers.video"]
kling = "ovf_kling.provider:KlingProvider"
```

```bash
pip install ovf-kling
```

## ComfyUI setup

1. Install [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
2. Download your model (Wan 2.1, HunyuanVideo, LTX-Video, etc.)
3. Export a workflow as **API JSON** (enable dev mode in ComfyUI settings)
4. Point `workflow:` in your config at the JSON file
5. Set `prompt_node_id` to the node ID of your text prompt input

## Workspace layout

```
workspace/
  runs/
    run_20240601_120000/
      images/
      videos/
      audio/
      metadata/
      logs/
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
