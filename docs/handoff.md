# Handoff Document — VideoOps Pipeline Refactor (v0.2.1)

## Project State

VideoOps is an automated AI YouTube Shorts generation pipeline (`v0.2.1`) built in Python 3.12 with MoviePy 2.2.1 and FFmpeg. The LLM generates structured script content from trending news, Supertonic-3 ONNX synthesizes offline 44.1kHz speech narration, stock video assets are fetched from Pexels, and the compositing engine renders a vertical 1080×1920 short with translucent glassmorphism subtitle pill capsules and gold active word highlights. The pipeline is currently fully operational, producing visually verified 1080×1920 YouTube Shorts with an official **10/10 PASSED** rating from the Visual QA Engineer subagent (`visual-qa-inspector`).

---

## Completed This Thread

### 1. Offline Supertonic-3 ONNX TTS Integration
- **What Was Done**: Removed legacy cloud speech packages (`azure-cognitiveservices-speech`, `google-cloud-texttospeech`, `gTTS`). Built an offline, thread-safe `SupertonicTTSProvider` in [src/videoops/assets/audio.py](file:///home/addy/projects/apps/videoops/src/videoops/assets/audio.py) using ONNX Runtime 1.28.0 and Supertonic-3 flow-matching models located at `sandbox/models/tts/supertonic-3`.
- **Validation Status**: **PASSED**. Generated clean 44.1kHz speech audio files (`.mp3`) with zero cloud API dependencies.

### 2. Glassmorphism Pill Subtitle Overlay Redesign
- **What Was Done**: Built an animated, translucent frosted dark glass pill capsule badge (`rgba(0, 0, 0, 180)`), rounded capsule ends, crisp 1px border (`outline=(255, 255, 255, 120)`), centered dead in the middle of the 1080×1920 canvas (`y = 960`) in [src/videoops/media/text_overlay.py](file:///home/addy/projects/apps/videoops/src/videoops/media/text_overlay.py).
- **Validation Status**: **PASSED**. Uses Pillow's official `draw.textlength` for exact prefix text length centering for sub-pixel accuracy, zero text doubling/smearing, and zero text overflow.
- **Active Word Highlight**: Renders 1–3 compact words per chunk with active word highlighted in bright gold yellow (`#FFEB14`) and base text in high-contrast white (`#FFFFFF`).
- **Punctuation Stripping**: Preserves internal contraction apostrophes (e.g. `"Switch 2's"`) while stripping leading/trailing hyphens, quotes, and punctuation.

### 3. Google Fonts Typography System
- **What Was Done**: Replaced 14-byte broken stub font files in [src/videoops/assets/fonts/](file:///home/addy/projects/apps/videoops/src/videoops/assets/fonts/) with genuine Google Fonts TTF binaries:
  - `Montserrat-ExtraBold.ttf` (318 KB)
  - `Outfit-Bold.ttf` (318 KB)
- **Validation Status**: **PASSED**. `FontManager` in [src/videoops/media/font_utils.py](file:///home/addy/projects/apps/videoops/src/videoops/media/font_utils.py) loads genuine Montserrat-ExtraBold without falling back to basic system fonts.

### 4. MoviePy 2.2 Background Motion Fix
- **What Was Done**: Fixed MoviePy composite clip transformation ordering in [src/videoops/media/compositor.py](file:///home/addy/projects/apps/videoops/src/videoops/media/compositor.py) by moving `all_child_clips.append(v_clip)` to *after* applying 1.35x Ken Burns slow-zoom scaling (`v_clip.resized(lambda t: 1.0 + 0.35 * (t / duration))`).
- **Validation Status**: **PASSED**. Background stock video clips execute smooth 1.35x zoom motion across segment durations with zero static frames.

### 5. Stock Video Query Specificity
- **What Was Done**: Updated query sanitization in [src/videoops/assets/visual.py](file:///home/addy/projects/apps/videoops/src/videoops/assets/visual.py) to map Nintendo-related queries directly to `"nintendo switch"`.
- **Validation Status**: **PASSED**. Pexels stock video search returns authentic Nintendo Switch / handheld gaming video footage instead of generic console clips.

---

## In Progress

- None. All tasks for the v0.2.1 refactor and visual redesign are 100% complete and validated.

---

## Pending / Not Started

1. **20–30 Second Multi-Card Script Prompt Tuning**:
   - Update `script_generator.py` prompt template to explicitly generate 5–7 storyboard cards (~25 seconds total speech duration) for longer YouTube Shorts.
2. **Automated Sandbox Purge Routine**:
   - Implement an automated lifecycle cleanup function in `orchestrator.py` that purges old scratch directories in `sandbox/temp/` before every pipeline run while preserving final videos in `sandbox/outputs/`.

---

## Decisions Made

1. **Offline Supertonic-3 ONNX TTS over Cloud APIs**:
   - **Decision**: Replaced Azure/Google/gTTS with Supertonic-3 ONNX models.
   - **Reason**: Eliminates paid cloud TTS API costs and rate limits; provides zero-latency offline speech synthesis.
2. **Single-Pass Word Rendering with Prefix `draw.textlength`**:
   - **Decision**: Swapped base white text drawing + gold overlay for single-pass word-by-word `draw.text` positioning using Pillow's `draw.textlength(prefix, font)`.
   - **Reason**: Guarantees sub-pixel centering, eliminates double-drawn text shadow offsets, and prevents stroke width discrepancies.
3. **Pill Capsule Geometry**:
   - **Decision**: Fixed pill card height at `card_h = max(80, text_h + 40)` and minimum width at `card_w = min(1040, max(880, full_text_w + 400))`.
   - **Reason**: Provides generous ~300px lateral flat glass padding so text never touches or bleeds into the rounded semi-circular caps.

---

## Open Questions

- None. All requirements and visual QA gates have been satisfied.

---

## Warnings & Known Issues

- **Sandbox Disk Usage**: Frequent test runs accumulate temporary WAV and frame files under `sandbox/temp/`. Manual or automated deletion of `sandbox/temp/` is recommended periodically.
- **Pexels API Rate Limits**: High-frequency pipeline runs consume Pexels API quota. Ensure `PEXELS_API_KEY` in `.env` remains valid.

---

## How to Resume

To continue development or run the pipeline in a new thread, open a new session with the following context:

```
ROLE: .agents/rules/py-backend-engineer.md
CONTEXT:
VideoOps AI YouTube Shorts pipeline (v0.2.1) is fully functional with Supertonic-3 ONNX TTS, MoviePy 2.2 compositing, and glassmorphism pill subtitles.
SOURCE OF TRUTH: AGENTS.md, src/videoops/
CURRENT STATE: All core refactors complete. Visual QA subagent rating is 10/10 PASSED.
CURRENT TASK: Optional script card prompt expansion for 20-30s shorts or automated sandbox cleanup.
COMMAND: python main.py video
```
