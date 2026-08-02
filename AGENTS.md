# AGENTS.md — videoops

## Rules Gate — READ THESE FIRST

`.agents/rules/` defines role-specific mandates that override defaults. Read the relevant rule file BEFORE starting any task and follow it verbatim:

| Task type | Rule file to load |
|-----------|--------------------|
| Any Python/backend code | `.agents/rules/py-backend-engieer.md` |
| Any LLM/prompt/agent work | `.agents/rules/senior-ai-engineer.md` |
| Any output validation / pipeline sign-off | `.agents/rules/visual-qa-engineer.md` |

For every change or run, the visual-qa gate applies: **assume every output is broken until frames are verified**.

---

## What This Repo Is

AI YouTube Shorts pipeline (`v0.2.0`). LLM writes the script → media assets fetched/synthesized → MoviePy+FFmpeg assembles a 1080×1920 vertical short → optional YouTube upload. Code that runs is only half the job; the **rendered video is the product**. If the frames are bad, the code is wrong, no matter how clean it looks.

## Layout

```
main.py                    # CLI entrypoint
src/videoops/
├── domain/        # Pure dataclasses/enums — ZERO external deps (hard rule)
├── story/         # LLM script generation (OpenAI-compatible client) + news fetch
├── assets/        # TTS fallback chain + stock/AI visual fetching
├── media/         # MoviePy/FFmpeg compositing, text overlays, frame extraction
├── publishing/    # YouTube OAuth upload
└── pipeline/      # ShortsPipelineOrchestrator — wires everything
docs/              # ALL specs & documentation live here
sandbox/           # ALL runtime output: outputs/ (final video) + temp/ (scratch) 
archive/           # holds the legacy `automation/` + `helper/`

## Commands

```sh
python main.py              # auto (video/image alternates by day-of-year)
python main.py video         # force video pipeline
python main.py image         # force image pipeline
```

## Operational Pitfalls — Before touching anything

- **Check for running work first.** Do NOT start a pipeline run if one is already in flight. Duplicate runs burn live API quota (TTS + LLM + stock APIs) and contend for the server. Confirm with a process check before any execution.
- **Never terminate a running process.** `server.txt` records a hard rule: if the GPU server is busy, STOP and report the blocker. Never kill a running job to make room.
- **Never run the long pipeline twice to "see".** One run = real spend + server time. Verify inputs once, run once.
- **Sandbox discipline.** Everything generated writes under `sandbox/` (`outputs/` and `temp/`). It is gitignored — never commit sandbox contents.
- **Never write output outside `sandbox/` and never commit** `.env` (live API keys) or `server.txt` (credentials). Both are gitignored; keep it that way.

## Quality Mandate

- **Quality is the first priority — no ceiling.** Every pipeline change is judged by the final rendered video, not by the code alone. If the output is merely "produced", it is not done.
- **Critique the frames brutally.** After any run, inspect sampled frames (the orchestrator extracts QA frames under `sandbox/temp/frame_samples_*/`) and the audio. Check: caption/text renders correctly, no overlap, transitions intentional, narration matches visuals, no black frames, pacing natural.
- **Do not approve** an output you only *assume* looks right. Apply the `visual-qa-engineer` rules before calling anything done.

## Config & Env

- `Settings` is a **module-level singleton** at `src/videoops/config.py:72` — not injectable; tests must monkeypatch. Imported by every layer.
- `.env` is loaded by `pydantic-settings`; the `load_dotenv()` in `main.py` is redundant (leave it out of new code).
- No `.env.example` exists — add one if you need to document env vars.
- `LLM_BASE_URL`/`LLM_MODEL` default to NVIDIA-compatible OpenAI endpoint (`meta/llama-3.1-8b-instruct`).

## Architecture Constraints

- 5-layer monolith; dependencies flow downwards, away from the orchestrator.
- `domain/` must stay dependency-free (stdlib only). Do not import pydantic, moviepy, requests, etc. there.
- No DI — services are constructed inline. This is a known limitation; keep it consistent unless explicitly asked to change it.
- Desktop/ffmpeg: FFmpeg must be on PATH (moviepy requirement). Python 3.11+.

---

## Current Status (v0.2.1 Refactor - Completed Work)

- **Offline Supertonic-3 ONNX TTS Integration**:
  - Uninstalled legacy cloud speech packages (`azure-cognitiveservices-speech`, `google-cloud-texttospeech`, `gTTS`).
  - Integrated offline thread-safe `SupertonicTTSProvider` in [src/videoops/assets/audio.py](file:///home/addy/projects/apps/videoops/src/videoops/assets/audio.py) using Supertonic-3 ONNX models.
- **Glassmorphism Pill Subtitle Overlay Engine**:
  - Redesigned frosted dark glass pill capsule badge (`rgba(0, 0, 0, 180)`), rounded capsule ends, crisp 1px border (`outline=(255, 255, 255, 120)`), centered dead in the middle of the 1080×1920 canvas (`y = 960`).
  - Built single-pass word rendering using Pillow's official `draw.textlength` with exact prefix text length centering for sub-pixel accuracy and zero text doubling/smearing.
  - Active word highlighted in bright gold yellow (`#FFEB14`) with high-contrast white base text (`#FFFFFF`).
  - Punctuation stripping handles leading/trailing hyphens while preserving internal contraction apostrophes (e.g. `"Switch 2's"`).
- **Google Fonts & Typography System**:
  - Replaced broken 14-byte stub fonts with genuine Google Fonts TTF binaries in [src/videoops/assets/fonts/](file:///home/addy/projects/apps/videoops/src/videoops/assets/fonts/): `Montserrat-ExtraBold.ttf` (318 KB) and `Outfit-Bold.ttf` (318 KB).
- **MoviePy 2.2 Background Motion Fix**:
  - Fixed background clip transformation ordering in [src/videoops/media/compositor.py](file:///home/addy/projects/apps/videoops/src/videoops/media/compositor.py) by moving `all_child_clips.append(v_clip)` *after* applying 1.35x Ken Burns slow-zoom motion (`v_clip.resized(lambda t: 1.0 + 0.35 * (t / duration))`).
- **Stock Video Query Specificity**:
  - Updated [src/videoops/assets/visual.py](file:///home/addy/projects/apps/videoops/src/videoops/assets/visual.py) query sanitization to query `"nintendo switch"` for Nintendo topics, eliminating generic/irrelevant stock video matches.
- **Visual QA Signoff**:
  - Verified by Visual QA Engineer subagent (`visual-qa-inspector`) with a **10/10 rating** and **PASSED verdict**.


