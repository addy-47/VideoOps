# videoops — Current Implementation Architecture

## Overview

`videoops` is an AI-powered YouTube Shorts automation system implemented as a **5-Layer Monolith** with unidirectional dependencies. The system generates scripts via LLM endpoints, fetches/synthesizes media assets, assembles vertical 1080×1920 video shorts using MoviePy 2.2+ & FFmpeg, and optionally uploads them to YouTube.

---

## Layer Diagram

```
[ Layer 5: Publishing Engine ]          src/videoops/publishing/
        ▲                                youtube.py
        │
[ Layer 4: Media Engine ]               src/videoops/media/
        ▲                                compositor.py, text_overlay.py, frame_extractor.py
        │
[ Layer 3: Asset Engine ]               src/videoops/assets/
        ▲                                audio.py, visual.py, thumbnail.py
        │
[ Layer 2: Story Engine ]               src/videoops/story/
        ▲                                client.py, script_generator.py, news_fetcher.py
        │
[ Layer 1: Core Domain ]                src/videoops/domain/
  (ZERO external deps)                   models.py — pure dataclasses & enums
```

---

## Layer 1 — Core Domain (`src/videoops/domain/`)

**Constraint**: ZERO external dependencies. Standard library only.

### Files

| File | Purpose |
|------|---------|
| `models.py` | Pure data schemas: `ScriptCard`, `ContentPackage`, `MediaAsset`, `ClipSegment`, `Timeline`, `VoiceStyle` (enum), `AssetType` (enum) |
| `__init__.py` | Public API re-exports for all domain models |

### Key Types

- **`ScriptCard`** (`frozen dataclass`): A single storyboard section — `text`, `duration`, `voice_style`, `background_query`
- **`ContentPackage`** (`frozen dataclass`): Complete LLM-generated package — `title`, `description`, `script_cards` (tuple), `thumbnail_hf_prompt`, `thumbnail_unsplash_query`
- **`MediaAsset`** (`frozen dataclass`): Handle to a local media file — `path`, `asset_type`, `duration`, `width`, `height`
- **`ClipSegment`** (`frozen dataclass`): A timed segment on the video timeline — `asset_path`, `start_time`, `duration`, `text`, `crossfade_in`, `crossfade_out`
- **`Timeline`** (`frozen dataclass`): Full composite video representation — `duration`, `segments` (tuple), `audio_path`, `title`
- **`VoiceStyle`** (`str, Enum`): `EXCITED`, `CALM`, `SERIOUS`, `CASUAL`, `NONE`
- **`AssetType`** (`str, Enum`): `AUDIO`, `IMAGE`, `VIDEO`

---

## Layer 2 — Story Engine (`src/videoops/story/`)

**Role**: Topic ingestion, LLM script generation, prompt management, storyboard parsing.

### Files

| File | Purpose |
|------|---------|
| `client.py` | `StoryLLMClient` — OpenAI-compatible LLM wrapper. Manages retries (exponential backoff), JSON extraction from markdown, and structured content generation. |
| `script_generator.py` | `generate_comprehensive_content()`, `generate_batch_video_queries()`, `generate_batch_image_prompts()` — LLM prompt engineering and response parsing into domain objects. |
| `news_fetcher.py` | `get_latest_news()` — Fetches top tech headline from NewsAPI or falls back to configured default topic. |
| `__init__.py` | Public API re-exports |

### Key Patterns

- **LLM Client**: Creates a new `OpenAI` client per `StoryLLMClient` instantiation (3 instantiations per pipeline run). Uses `response_format={"type": "json_object"}` for NVIDIA-compatible endpoints.
- **JSON Parsing**: Regex-based extraction from markdown code blocks (` ```json ... ``` `) and bare `{...}` objects. Non-greedy matching not used — potential correctness issue.
- **Retry Logic**: Exponential backoff (`2^attempt` seconds) up to 3 retries for LLM calls.

---

## Layer 3 — Asset Engine (`src/videoops/assets/`)

**Role**: Audio TTS fallback chain and visual stock/AI fetching.

### Files

| File | Purpose |
|------|---------|
| `audio.py` | `TTSProvider` — Three-tier TTS fallback: Google Cloud TTS → Azure Speech → gTTS. Applies 1.18× speech rate speedup via FFmpeg `atempo` filter. |
| `visual.py` | `VisualAssetProvider` — Three-tier visual fallback per asset type: Pexels → Pixabay → HuggingFace FLUX → Unsplash → solid color fallback. |
| `thumbnail.py` | `ThumbnailGenerator` — Creates 1080×1920 YouTube Shorts thumbnails with styled rounded-pill title overlays using Pillow. |
| `__init__.py` | Public API re-exports |

### Key Patterns

- **TTS Fallback Chain**: Google Cloud (with `speaking_rate=1.10`) → Azure (`en-US-JennyNeural`) → gTTS (`en`, `slow=False`). Speedup applied post-synthesis via `ffmpeg -filter:a atempo=1.18`.
- **Visual Fallback Chain**: Pexels video → Pixabay video → HuggingFace FLUX image → Pexels image → Unsplash → solid dark fallback image.
- **Filename Generation**: Uses `hash(text) & 0xFFFFFFFF` for cache keys — **non-deterministic across Python processes** due to `PYTHONHASHSEED` randomization.
- **Font Loading**: Each `create_text_image()` call retries three font paths sequentially (`DejaVuSans-Bold.ttf`, `FreeSansBold.ttf`, `LiberationSans-Bold.ttf`) with no caching.

---

## Layer 4 — Media Engine (`src/videoops/media/`)

**Role**: MoviePy 2.2+ / FFmpeg video compositing, text overlays, frame extraction.

### Files

| File | Purpose |
|------|---------|
| `compositor.py` | `VideoCompositor` — Renders `Timeline` domain objects into MP4 files. Enforces RAM-based adaptive thread/preset selection, `ExitStack` cleanup, and `psutil`-based resource detection. |
| `text_overlay.py` | `TextOverlayBuilder` — Generates 1080×1920 PNG overlay images with rounded-pill containers, word-by-word highlighting, drop shadows, and gold accent strokes. |
| `frame_extractor.py` | `extract_video_frames()` — Extracts JPEG frames at specified timestamps for visual QA inspection. |
| `__init__.py` | Public API re-exports |

### Key Patterns

- **Rendering**: Uses `ExitStack` for all MoviePy clip lifecycle management. Applies Ken Burns zoom effect for static images. Word-by-word caption overlays generated as individual PNG files then composited.
- **Adaptive Encoding**: RAM thresholds determine FFmpeg preset and thread count:
  - >8 GB RAM → `preset="fast"`, `threads = cores - 2`
  - >4 GB RAM → `preset="veryfast"`, `threads = min(4, cores // 2)`
  - ≤4 GB RAM → `preset="ultrafast"`, `threads = min(2, cores // 4)`
- **Bug**: Dynamic preset computation (lines 102–110) is dead code — line 124 hardcodes `preset="veryfast"` instead of using the computed `preset` variable.

---

## Layer 5 — Publishing Engine (`src/videoops/publishing/`)

**Role**: YouTube API non-interactive OAuth upload and thumbnail setting.

### Files

| File | Purpose |
|------|---------|
| `youtube.py` | `YouTubePublisher` — Handles OAuth credential construction, video upload via `google-api-python-client`, and custom thumbnail setting. |
| `__init__.py` | Public API re-exports |

### Key Patterns

- **OAuth**: Reads `YOUTUBE_ACCESS_TOKEN`, `YOUTUBE_REFRESH_TOKEN`, `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET` from environment at upload time (not at import time).
- **Upload**: Uses `MediaFileUpload` with `chunksize=-1` (single-request upload, defeats resumable upload purpose) and `resumable=True`.
- **Hardcoded Metadata**: Tags `["Shorts", "AI", "Tech"]` and category `"28"` (Science & Technology) are hardcoded.

---

## Orchestrator (`src/videoops/pipeline/`)

**Role**: Coordinates the full end-to-end pipeline workflow across all 5 layers.

### Files

| File | Purpose |
|------|---------|
| `orchestrator.py` | `ShortsPipelineOrchestrator` — Single 185-line `run()` method orchestrating: news fetching → LLM script generation → parallel TTS + visual asset acquisition → audio concatenation → thumbnail generation → video compositing → frame extraction → YouTube upload. |
| `__init__.py` | Public API re-exports |

### Pipeline Flow

```
1. News Fetching (Layer 2)          → get_latest_news()
2. Script Generation (Layer 2)      → generate_comprehensive_content(topic)
3. Parallel Asset Acquisition       → TTS synthesis + visual fetching (ThreadPoolExecutor)
4. Audio Concatenation              → _concat_audio_files()
5. Thumbnail Generation (Layer 3)   → ThumbnailGenerator.generate()
6. Video Compositing (Layer 4)      → VideoCompositor.render()
7. Frame Extraction (Layer 4)       → extract_video_frames()
8. YouTube Upload (Layer 5)         → YouTubePublisher.publish()
```

### Concurrency Model

- `ThreadPoolExecutor(max_workers=max(1, num_cards * 2))` for parallel TTS + visual fetching
- TTS futures and visual futures submitted together, collected separately via `as_completed()`
- No upper bound on thread count — unbounded by card count

---

## Configuration (`src/videoops/config.py`)

- **`Settings`** (Pydantic `BaseSettings`): Parses `.env` file and environment variables
- **Singleton**: `settings = Settings()` instantiated at module import time
- **Key Settings**: `LLM_BASE_URL`, `LLM_MODEL`, `NVIDIA_API_KEY`, `LLM_API_KEY`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `NEWS_API_KEY`, `HUGGINGFACE_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`, `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`, `YOUTUBE_TOPIC`, `ENABLE_YOUTUBE_UPLOAD`, `OUTPUT_DIR`, `TEMP_DIR`
- **Properties**: `api_key` (resolves NVIDIA_API_KEY or LLM_API_KEY), `project_root`, `resolved_output_dir`, `resolved_temp_dir`

---

## Entry Point (`main.py`)

- Loads `.env` via `python-dotenv` (redundant — `pydantic-settings` also loads `.env`)
- Parses CLI argument for `mode` (`auto`, `video`, `image`)
- Instantiates `ShortsPipelineOrchestrator` and calls `run(mode=mode)`
- No validation of `mode` argument — invalid values silently default to image mode

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `openai` | ≥1.0.0 | LLM API client |
| `pydantic` | ≥2.0.0 | Settings validation |
| `pydantic-settings` | ≥2.0.0 | Environment-based settings |
| `moviepy` | ≥2.2.1 | Video composition |
| `Pillow` | ≥10.4.0 | Image/overlay rendering |
| `numpy` | ≥2.2.3 | Array operations (transitive) |
| `requests` | ≥2.32.4 | HTTP client for stock APIs |
| `python-dotenv` | ≥1.0.1 | .env loading (redundant with pydantic-settings) |
| `gTTS` | ≥2.5.4 | TTS fallback |
| `google-cloud-texttospeech` | ≥2.24.0 | Google TTS provider |
| `google-api-python-client` | ≥2.160.0 | YouTube upload |
| `google-auth` | ≥2.38.0 | OAuth credentials |
| `google-auth-oauthlib` | ≥1.2.1 | OAuth flow |
| `azure-cognitiveservices-speech` | ≥1.42.0 | Azure TTS provider |
| `tqdm` | ≥4.67.1 | **Unused** |
| `psutil` | ≥5.9.0 | RAM detection for encoding |

---

## Key Architectural Observations

1. **Strict layer isolation** is defined in `.agents/rules/architecture.md` but not fully enforced at the code level — `config.py` is imported by every layer, and `pipeline/orchestrator.py` imports directly from layers 3, 4, and 5.
2. **No dependency injection** — all services are instantiated directly inside the orchestrator and other classes, making testing impossible without monkeypatching.
3. **Global singleton** `settings` in `config.py` creates hidden coupling across all layers.
4. **No test suite** exists despite `pytest` being listed as a dev dependency.
5. **`python-dotenv` is redundant** — `pydantic-settings` already handles `.env` loading.