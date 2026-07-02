# yt-aotomation — Agent Guide

## What this is

AI-powered YouTube Shorts automation. Generates scripts (Gemini `gemini-2.5-flash-lite` via `google-genai` SDK), assembles video/image clips (MoviePy 2.1.2), adds TTS voiceover (Google Cloud → Azure → gTTS fallback), and optionally uploads to YouTube.

Pure Python 3 project. No monorepo tooling, no build step, no Docker, no CI.

## Architecture

```
main.py                        ← entrypoint
├── automation/                ← core pipeline (content gen, creators, upload, auth)
└── helper/                    ← utilities (text, audio, fetch, image, blur, crossfade, etc.)
```

- `main.py`: orchestrates the full pipeline. Calls `get_creator_for_day()` which alternates between **image-based** (`YTShortsCreator_I`, even days) and **video-based** (`YTShortsCreator_V`, odd days).
- `automation/`: content generation (Gemini), Shorts creators (video/image), YouTube upload/auth, thumbnail gen, parallel rendering.
- `helper/`: text/animation clips, TTS with fallback chain, stock video/image fetching, crossfade concatenation, blur effects, system resource monitoring, news fetching.

Design pattern everywhere: **fallback chains** — if the primary method fails, the code tries alternatives before giving up (TTS: Google → Azure → gTTS; images: HF model → fallback HF → Unsplash → Pexels; rendering: parallel → sequential → emergency copy).

## Setup

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**API keys** (in `.env` — already present on this machine, **never commit**):
`GEMINI_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS` (points to `lazycreator-1.json`), `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `NEWS_API_KEY`, `AZURE_SPEECH_KEY`/`AZURE_SPEECH_REGION`, `HF_API_TOKEN`, `ENABLE_YOUTUBE_UPLOAD`.

## Commands

| Action | Command |
|--------|---------|
| Run (auto-select creator by day parity) | `python main.py` or `.venv/bin/python main.py` |
| Force video-based creator | `python main.py video` |
| Force image-based creator | `python main.py image` |
| Cron execution | `./run.sh` (uses `SCRIPT_DIR` instead of hardcoded path) |
| Debug mode | `DEBUG_MODE=true python main.py` |
| Enable upload | `ENABLE_YOUTUBE_UPLOAD=true python main.py` |
| Verify API keys | `python _verify_keys.py` |

Output goes to `ai_shorts_output/` with daily rotated logs in `logs/`.

## Pass 1 cleanup — what was done

- **`_init_.py` → `__init__.py`**: Both packages now have proper `__init__.py` files.
- **`schedule.py`**: Removed (entirely commented-out dead code).
- **Hardcoded font paths**: All 7 references now use `Path(__file__).resolve().parent.parent / "packages/fonts/default_font.ttf"` — no more absolute paths tied to the old repo location.
- **`.env`**: `GOOGLE_APPLICATION_CREDENTIALS` updated to current repo path.
- **`run.sh`**: Uses `SCRIPT_DIR` instead of hardcoded old path.
- **Circular import fixed**: `helper/audio.py` ↔ `automation/voiceover.py` — broken by moving the import inside the methods that need it.
- **Bare `except:`**: All 9 occurrences replaced with `except Exception:`.
- **`logging.basicConfig()`**: Removed from 5 files that set it at module level (main.py owns logging setup).
- **`load_dotenv()`**: Removed from 14 files (now called once in `main.py` before project imports).
- **Dead code removed**: `fetch_image_unsplash` (defunct method using `self` outside a class), `get_keywords()` (unused NLTK function), test blocks in `content_generator.py` and `thumbnail.py`, unused imports (`textwrap`, `wraps`, `multiprocessing`, `nltk`, `dotenv` in various files).
- **`requirements.txt`**: Stripped from 78 → 16 packages. Removed `opencv-python`, `PyAudio`, `pydub`, `scipy`, `sentry-sdk`, `Flask` (and 10+ other unused transitive deps), `logging==0.4.9.6` (name collision with stdlib), `ffmpeg-python`, `httpx`, `regex`, `future`. Removed dev tools (`black`, `flake8`, `isort`, `pytest`) — no pyproject.toml yet. Added missing `psutil` and `google-cloud-secret-manager`.
- **API key verification**: `_verify_keys.py` checks all keys. See current status below.

## Pass 2 — OpenAI → Gemini migration + MoviePy 2.x bug fixes + pipeline completion

### What was done
- **OpenAI → Gemini**: Removed `openai` SDK entirely. Replaced with `google-genai` SDK (v2.8.0). All 3 content generation functions now use `from google import genai` with `client.models.generate_content()`.
- **JSON structured output**: Uses `response_mime_type='application/json'` for JSON responses from Gemini.
- **Model config**: Model defaults to `gemini-2.5-flash-lite`, configurable via `GEMINI_MODEL` env var.
- **`.env`**: `OPENAI_API_KEY` removed, `GEMINI_API_KEY` added.
- **`_verify_keys.py`**: Now tests Gemini API with live call (temporary).
- **Dead files deleted**: `automation/_init_.py`, `helper/_init_.py`, `automation/schedule.py`.

### MoviePy 2.x compatibility fixes (10 files modified)
| Bug | File | Fix |
|-----|------|-----|
| `'ImageClip' object has no attribute 'crop'` | `helper/image.py:493` | `.crop()` → `.cropped()` |
| `max_workers must be greater than 0` | 10 spots across `fetch.py`, `text.py`, `process.py`, `image.py`, `audio.py`, `parallel_tasks.py` | `max(1, os.cpu_count() or 1)` guard |
| `y1 must be >= y0` text geometry | `helper/text.py:74-75` | Clamped slide/slide_out positions |
| `with_effects()` tuple → list | `helper/text.py:496,498` | `(CrossFadeIn(...))` → `[CrossFadeIn(...)]` |
| `IndentationError` (pre-existing) | `helper/text.py:503` | Fixed 11-space → 10-space indent |
| Word-by-word crossfade failure | `helper/text.py:517-521` | Added 2nd fallback (raw concat) |
| Hardcoded `worker_count = 3` | `helper/memory.py:112` | Removed override |
| Crossfade in MoviePy 2.x | `helper/crossfade.py:221-247` | Removed old `crossfade_duration` kwarg; uses per-clip `CrossFadeIn`/`CrossFadeOut` + `method="compose"` |
| `load_dotenv` undefined | `automation/thumbnail.py:32` | Removed redundant call |
| MoviePy version upgrade | `requirements.txt` | `moviepy>=2.1.2` → `moviepy>=2.2.1` |

### Pipeline verification (both creators produce valid output)
| Pipeline | Duration | Size | Thumbnail |
|----------|----------|------|-----------|
| Image-based (even days) | 29.53s, 1080×1920, ~30fps, 39MB | ✅ |
| Video-based (odd days) | 22.96s, 1080×1920, 30fps, 24MB | ✅ (471K) |

Multiple Gemini content generation functions work reliably with `gemini-2.5-flash-lite`. Image fallback chain (HF → Unsplash → Pexels) works. Crossfading in MoviePy 2.2.1 is functional. YouTube upload blocked by port 8080 conflict (only matters with `ENABLE_YOUTUBE_UPLOAD=true`).

## Next steps (unresolved)

- **Remove `_verify_keys.py`** — temporary verification script, no longer needed for production.
- **Pass 3: Code deduplication** — `shorts_maker_I.py` and `shorts_maker_V.py` share ~70% identical code (rendering pipeline, crossfading, audio/timing logic). Extract shared base class or utility module.
- **Pass 4: Directory restructuring** — move project into `src/` layout for cleaner packaging.
- **YouTube upload** — port 8080 conflict needs resolution if upload is desired.
- **`pyproject.toml`** — add proper project metadata, dev tool configs (ruff, pytest).

## Current API key status (as of Pass 2)

| Key | Status |
|-----|--------|
| `GEMINI_API_KEY` | ✅ Present, user-provided |
| `GOOGLE_APPLICATION_CREDENTIALS` | ✅ File found, path updated |
| `PEXELS_API_KEY` | ✅ Working |
| `PIXABAY_API_KEY` | ✅ Working |
| `NEWS_API_KEY` | ✅ Working |
| `HUGGINGFACE_API_KEY` | ✅ Present |
| `AZURE_SPEECH_KEY`/`AZURE_SPEECH_REGION` | ⚠️ Not set (optional, gTTS fallback) |

## Model references

Gemini model defaults to `gemini-2.5-flash-lite`, configurable via `GEMINI_MODEL` env var.
Used in `main.py` (2 locations) and `automation/content_generator.py` (3 function defaults).

## Operational quirks

- **Imports and `.env`**: `main.py` calls `load_dotenv()` BEFORE importing project modules, so env vars are available at module-load time.
- **`run.sh` auto-commits** — before every cron run, it does `git add . && git commit --allow-empty`. The repo assumes this is the primary execution path.
- **Day parity** — creator type alternates on even/odd day-of-year. Override with `main.py video` or `main.py image` for testing.
- **70% code duplication** between `shorts_maker_I.py` and `shorts_maker_V.py` — not addressed yet.
- **`requirements.txt`**: CRLF line endings fixed to Unix.
