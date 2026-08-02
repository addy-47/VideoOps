# VideoOps

AI-powered YouTube Shorts automation pipeline (`v0.2.0`). An LLM writes the script, media assets are fetched or synthesized, and MoviePy + FFmpeg assemble a 1080×1920 vertical short with animated word-by-word captions, crossfade transitions, and a generated thumbnail. Optional YouTube upload.

## How It Works

```
LLM script (OpenAI-compatible) ──▶ TTS voiceover (Google Cloud → Azure → gTTS)
                              ──▶ visuals (Pexels → Pixabay → HuggingFace → fallback)
        │
        ▼
MoviePy/FFmpeg composite ──▶ 1080×1920 MP4 + thumbnail ──▶ (optional) YouTube upload
```

Pipeline stages (orchestrated by `ShortsPipelineOrchestrator` in `src/videoops/pipeline/orchestrator.py`):

1. **Story** — fetch a topic (optionally from NewsAPI) and generate a script package via an OpenAI-compatible LLM.
2. **Assets** — synthesize per-card TTS audio and fetch videos/images in parallel.
3. **Composition** — build a timeline, render with MoviePy/FFmpeg, and extract sample frames for QA.
4. **Publish** — optionally upload video + thumbnail to YouTube.

## Project Structure

```
main.py                     # CLI entrypoint
src/videoops/
├── domain/                 # Pure dataclasses/enums (ZERO external deps — hard rule)
├── story/                  # LLM script generation + news fetch
├── assets/                 # TTS fallback chain + stock/AI visual fetching
├── media/                  # MoviePy/FFmpeg compositing, text overlays, frames
├── publishing/             # YouTube OAuth upload
└── pipeline/               # ShortsPipelineOrchestrator
docs/                       # Specs & documentation (architecture, audit report)
sandbox/                    # All runtime output — outputs/ (final video), temp/ (scratch)
archive/                    # Legacy automation/ + helper/ implementation (read-only reference)
```

The old `automation/` + `helper/` implementation is preserved in `archive/` as read-only reference. Do not build on it — live code lives under `src/videoops/`.

## Requirements

- Python 3.11+
- **FFmpeg** on PATH (MoviePy requirement): `sudo apt install ffmpeg`
- Optional: a credentials JSON for Google Cloud TTS (`GOOGLE_APPLICATION_CREDENTIALS`), Azure Speech keys, or stock/visual API keys — the pipeline falls back to gTTS and a solid-color image when these are missing, so it runs with no keys at all.

## Setup

```sh
python -m venv .venv
source .venv/bin/activate
pip install -e .            # or: pip install -r requirements.txt
```

### Environment variables (`.env`)

| Variable | Purpose | Required |
|----------|---------|----------|
| `LLM_BASE_URL` | OpenAI-compatible endpoint (default: NVIDIA `https://integrate.api.nvidia.com/v1`) | no |
| `LLM_MODEL` | Model name (default: `meta/llama-3.1-8b-instruct`) | no |
| `NVIDIA_API_KEY` / `LLM_API_KEY` | LLM API key | yes for script generation |
| `NEWS_API_KEY` | NewsAPI headline sourcing (falls back to `YOUTUBE_TOPIC`) | no |
| `PEXELS_API_KEY`, `PIXABAY_API_KEY` | Stock video/image search | no |
| `HUGGINGFACE_API_KEY` | AI image generation (FLUX) | no |
| `GOOGLE_APPLICATION_CREDENTIALS`, `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` | TTS providers (fall back to gTTS) | no |
| `ENABLE_YOUTUBE_UPLOAD` | `true`/`false` — gates the publish step | no |
| `YOUTUBE_ACCESS_TOKEN`, `YOUTUBE_REFRESH_TOKEN`, `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET` | OAuth credentials for upload | only when publishing |
| `YOUTUBE_TOPIC` | Default topic fallback | no |
| `OUTPUT_DIR`, `TEMP_DIR` | Output/scratch dirs (default `sandbox/outputs`, `sandbox/temp`) | no |

**Note:** no `.env.example` exists yet — add one if you add new env vars.

## Usage

```sh
python main.py              # auto (video/image alternates by day-of-year)
python main.py video        # force video pipeline
python main.py image        # force image pipeline
```

Outputs go to `sandbox/`:

- `sandbox/outputs/yt_short_*.mp4` — final rendered short
- `sandbox/temp/thumbnail_*.jpg` — generated thumbnail
- `sandbox/temp/frame_samples_*/` — QA frames sampled from the rendered video

## Quality Guidance

The rendered video is the product. After any run, inspect the sampled frames under `sandbox/temp/frame_samples_*/`: caption rendering and overlap, transition intent, narration/visual alignment, black frames, pacing. See `docs/audit-report.md` for known issues and `docs/architecture.md` for implementation details.

## Documentation

- `docs/architecture.md` — current implementation structure
- `docs/audit-report.md` — code audit (101 findings: bugs, security, performance, testing gaps)

## License

MIT