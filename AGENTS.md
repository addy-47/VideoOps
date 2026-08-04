# AGENTS.md — videoops

## Rules Gate — READ THESE FIRST

`.agents/rules/` defines role-specific mandates that override defaults. Read the relevant rule file BEFORE starting any task and follow it verbatim:

| Task type | Rule file to load |
|-----------|--------------------|
| Any Python/backend code | `.agents/rules/py-backend-engieer.md` |
| Any LLM/prompt/agent work | `.agents/rules/senior-ai-engineer.md` |
| Any HTML/CSS/JS canvas or frontend design | `.agents/rules/frontend-engineer.md` |
| Any output validation / pipeline sign-off | `.agents/rules/visual-qa-engineer.md` |

For every change or run, the visual-qa gate applies: **assume every output is broken until frames are verified**.

---

## What This Repo Is

AI YouTube Shorts pipeline (`v0.2.3` $\rightarrow$ `v1.0` Architecture Phase). LLM writes the script $\rightarrow$ Code-to-Canvas HTML/CSS/JS + GSAP scenes rendered via Playwright $\rightarrow$ MoviePy+FFmpeg assembles 1080×1920 vertical short with TTS, SFX, and BGM $\rightarrow$ optional YouTube upload. Code that runs is only half the job; the **rendered video is the product**. If the frames are bad, the code is wrong, no matter how clean it looks.

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
analysis/          # 20 downloaded benchmark Shorts + STT transcripts & storyboards
templates/         # Ground-truth 1:1 benchmark Short codebases (4-5 full Shorts)
docs/
└── specs/         # System specifications (vision-spec.md, architecture-spec.md)
sandbox/           # ALL runtime output: outputs/ (final video) + temp/ (scratch) 
archive/           # holds the legacy `automation/` + `helper/`
```

## Quality Mandate & Anti-Slop Enforcement

- **Quality is the first priority — no ceiling.** Every pipeline change is judged by the final rendered video, not by the code alone. If the output is merely "produced", it is not done.
- **Mandatory `DESIGN.md` Requirement**: Every template codebase must contain a `DESIGN.md` defining its mode, color palette tokens, typography pairs, and signature motion elements before any canvas code is written.
- **Zero AI Slop Directives**: No static screenshot fallbacks, no generic flexbox cards with plain fade/slide tweens, and no simplifying visual/animation complexity because it is difficult.
- **Skill Consultation Gate**: Before writing canvas code, active deep-dives into frontend design skills (`impeccable`, `frontend-design`, `web-animation-design`, `gsap-core`, `gsap-timeline`) are strictly required.
- **Critique the frames brutally.** After any run, inspect sampled frames and audio. Apply `visual-qa-engineer` and `frontend-engineer` rules before calling anything done.

## Operational Pitfalls — Before touching anything

- **Check for running work first.** Do NOT start a pipeline run if one is already in flight. Duplicate runs burn live API quota (TTS + LLM + stock APIs) and contend for the server. Confirm with a process check before any execution.
- **Never terminate a running process.** `server.txt` records a hard rule: if the GPU server is busy, STOP and report the blocker. Never kill a running job to make room.
- **Never run the long pipeline twice to "see".** One run = real spend + server time. Verify inputs once, run once.
- **Sandbox discipline.** Everything generated writes under `sandbox/` (`outputs/` and `temp/`). It is gitignored — never commit sandbox contents.
- **Never write output outside `sandbox/` and never commit** `.env` (live API keys) or `server.txt` (credentials). Both are gitignored; keep it that way.

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

## Current Status (v0.2.3 & VideoOps 1.0 Vision/Specs Phase)

- **Benchmark Shorts Extraction & Analysis**:
  - Downloaded 10 KodeKloud and 10 InsiderForce top Shorts into `analysis/`.
  - Processed 3-second frame extraction for all 20 videos into dedicated subdirectories.
  - Generated timestamped STT transcripts (`transcript.txt` / `transcript.json`) using `faster-whisper`.
  - Generated production-grade storyboards (`storyboard.md`) using `gemma4:e4b` (128K context window via remote Ollama at `http://100.86.62.14:11434`).
- **VideoOps 1.0 Specifications (Code-to-Canvas Architecture)**:
  - Created [docs/specs/vision-spec.md](file:///home/addy/projects/apps/videoops/docs/specs/vision-spec.md): Product vision, Code-to-Canvas paradigm, and quality requirements.
  - Created [docs/specs/architecture-spec.md](file:///home/addy/projects/apps/videoops/docs/specs/architecture-spec.md): Multi-Agent topology (Producer, Creative Director, Visual Lead + CLI subagent delegation, Media Lead, QA Lead).
- **Frontend Engineer Role & Skills**:
  - Registered [.agents/rules/frontend-engineer.md](file:///home/addy/projects/apps/videoops/.agents/rules/frontend-engineer.md) referencing `gsap-core`, `gsap-timeline`, `frontend-design`, `web-animation-design`, and `impeccable`.
- **Ground-Truth Benchmark Templates Directory**:
  - Initialized [templates/](file:///home/addy/projects/apps/videoops/templates/README.md) directory to house 4–5 complete, 1:1 ground-truth code reproductions of selected benchmark Shorts prior to multi-agent pipeline development.
