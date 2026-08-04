# Architecture Spec (Draft) — VideoOps 1.0

**Name & Concept**
This document outlines the conceptual multi-agent hierarchy, component boundaries, data flow, and feedback loops that constitute the **VideoOps 1.0** production engine.

> [!NOTE]
> This is an **initial architectural draft**. Final technical specifications, class models, and API interfaces will be finalized after the Ground-Truth Benchmark Short phase (`templates/`) is complete.

---

## High-Level System Topology

```
                  ┌──────────────────────────────┐
                  │        User / Config         │
                  └──────────────┬───────────────┘
                                 │ config.yaml
                                 ▼
                  ┌──────────────────────────────┐
                  │        Producer Agent        │
                  └──────────────┬───────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │ creative_brief.md  │ script.md          │ design_system.json
            ▼                    ▼                    ▼
      ┌─────────────────────────────────────────────────────┐
      │               Creative Director Agent               │
      │                   (Orchestrator)                    │
      └───────┬─────────────────────────────┬───────────────┘
              │                             │
              │ Storyboard Scene Specs      │ Storyboard Audio Specs
              ▼                             ▼
   ┌────────────────────┐        ┌────────────────────┐
   │    Visual Lead     │        │     Media Lead     │
   └──────────┬─────────┘        └──────────┬─────────┘
              │                             │
     (Delegates via CLI)                    │ Synthesizes TTS, SFX, BGM
              │                             │ & Composites Canvases
              ▼                             ▼
   ┌────────────────────┐        ┌────────────────────┐
   │ CLI Coding Agents  │        │   Draft Video MP4  │
   │(agy / opencode...) │        └──────────┬─────────┘
   └──────────┬─────────┘                   │
              │                             │
              ▼                             │
     Captured Canvas Video                  │
            │                               │
            └───────────────┬───────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │          QA Lead          │
              └─────────────┬─────────────┘
                            │
               ┌────────────┴────────────┐
               │                         │
        [PASS] ▼                         ▼ [FAIL + Bug Report]
        Final Output              (Loops back to Director)
```

---

## Component Boundaries & Responsibilities

### 1. Producer Agent (Entry Point)
* **Inputs**: User configuration (`config.yaml`), topic, script outline, aspect ratio, target length, tone, aesthetic guidelines.
* **Responsibilities**:
  * Formulate the overarching creative vision and production strategy.
  * Dynamically create the project's visual identity, typography tokens, color palettes, and component styles.
  * Generate structured intermediate production artifacts:
    1. `creative_brief.md`: Target audience, hook strategy, tone, visual direction.
    2. `script.md`: Narrator voiceover lines with target segment durations.
    3. `design_system.json` (or `.md`): Color palette tokens, font choices, CSS variables, badge designs, and animation timing constants.
* **Outputs**: `creative_brief.md`, `script.md`, `design_system.json`.

### 2. Creative Director Agent (Orchestrator)
* **Inputs**: Producer artifacts (`creative_brief.md`, `script.md`, `design_system.json`).
* **Responsibilities**:
  * Convert script and brief into a production-grade **Storyboard Specification** (`storyboard_spec.json`).
  * Define scene-by-scene timing, camera framing, typography overlays, visual scene layout, and audio cues.
  * Direct and orchestrate the **Visual Lead** and **Media Lead** subagents.
  * Process feedback/bug reports from the **QA Lead** and issue targeted revision directives.
* **Outputs**: `storyboard_spec.json`, revision directives.

### 3. Visual Lead Agent (Canvas Director)
* **Inputs**: Scene storyboard specs from `storyboard_spec.json`, `design_system.json`.
* **Responsibilities**:
  * Direct the creation of HTML/CSS/JS (GSAP animated) web canvases for each storyboard scene.
  * **Dynamic Token Enforcement**: Ensure all CSS styles, colors, typography, and badges bind strictly to `design_system.json` tokens without hardcoded rules.
  * **CLI Subagent Delegation**: Delegate raw frontend code writing to external CLI coding agents (e.g. `antigravity-cli`, `opencode`, `claude-code`) via dedicated skills (e.g. `agy-subagent`).
  * **Review & Verification**: Inspect generated canvas code against `design_system.json` and `storyboard_spec.json` for design system compliance, visual continuity, and smooth GSAP timing.
  * **Canvas Recording**: Capture the approved GSAP HTML canvas in headless Playwright/Puppeteer at 60 FPS in 1080×1920 vertical resolution.
* **Outputs**: Recorded canvas video clips (`.mp4` / `.webm`) per scene segment.

### 4. Media Lead Agent (Audio Synthesis & Compositing)
* **Inputs**: `storyboard_spec.json`, timestamped script, recorded canvas video clips.
* **Responsibilities**:
  * **Voiceover Synthesis**: Generate clear, high-quality TTS narration audio with exact timing matching the script segments.
  * **Sound Design (SFX / Foley)**: Overlay sound effects (clicks, pops, UI whooshes, transition swooshes) at key visual motion triggers.
  * **Audio Ducking & BGM**: Mix background music (BGM) with automatic audio ducking under voiceover lines.
  * **Final Compositing**: Merge canvas video clips, overlay typography badges, TTS narration, SFX, and BGM using MoviePy / FFmpeg.
* **Outputs**: Rendered candidate video file (`draft_output.mp4`).

### 5. QA Lead Agent (Closed-Loop Evaluator)
* **Inputs**: `draft_output.mp4`, `creative_brief.md`, `storyboard_spec.json`.
* **Responsibilities**:
  * Extract keyframes and audio tracks from `draft_output.mp4`.
  * Perform automated visual & multimodal quality verification:
    - **Legibility & Contrast**: Ensure text overlays and subtitles are crisp and readable.
    - **Pacing & Hook**: Verify the first 3 seconds hook the viewer effectively.
    - **Audio-Visual Alignment**: Confirm voiceover, kinetic text, and SFX trigger synchronously.
  * **Verdict**:
    - **PASS**: Authorize final output.
    - **FAIL**: Generate a structured `qa_bug_report.md` specifying exact timestamps and failing visual/audio criteria, then loop back to the **Creative Director**.
* **Outputs**: `qa_pass_certificate` OR `qa_bug_report.md`.

---

## Data Contracts & Interfaces (Conceptual)

1. `config.yaml` $\rightarrow$ Producer Agent
2. `creative_brief.md`, `script.md`, `design_system.json` $\rightarrow$ Creative Director
3. `storyboard_spec.json` $\rightarrow$ Visual Lead & Media Lead
4. Scene HTML/CSS/JS + `agy` CLI subagent $\rightarrow$ Recorded Canvas Clips
5. Canvas Clips + TTS + SFX + BGM $\rightarrow$ `draft_output.mp4`
6. `draft_output.mp4` $\rightarrow$ QA Lead $\rightarrow$ PASS or `qa_bug_report.md` (loop back)

---

## Out of Scope (Architectural Constraints)

- **Static Aesthetic Rule Encoding**: No agent rules or pipeline modules encode fixed CSS colors, static fonts, or hardcoded visual component styles.
- **Direct Monolithic Code Authorship**: No single agent writes the full pipeline and canvas frontend code simultaneously.
- **In-Memory Unbounded State**: All communication between agents is mediated through file artifacts (`.json`, `.md`, `.mp4`).

---

## Open Questions

- What specific CLI interface parameters should be standardized across different coding subagents (`agy`, `opencode`, `claude-code`)?
- Should Playwright record raw PNG frame sequences or stream directly to FFmpeg pipe for 60 FPS video recording?
