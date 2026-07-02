# 🎬 VideoOps

**VideoOps** is an advanced, fully-automated AI video generation and orchestration pipeline. It generates scripts, collects matching media assets (images/videos), synthesizes text-to-speech (TTS) voiceovers, applies professional transitions and dynamic word-by-word text animations, and renders fully-produced YouTube Shorts ready for publication.

---

## ✨ Features

- **Dynamic Content Selection**: Chooses optimal formats by alternating between **Image-Based** creators (`YTShortsCreator_I`, even days) and **Video-Based** creators (`YTShortsCreator_V`, odd days).
- **Automated Content Generation**: Utilizes Google Gemini (`gemini-2.5-flash-lite` via `google-genai` SDK) to write engaging short-form scripts, optimized search queries, and tailored image prompts.
- **Robust Fallback Chains**:
  - **Text-to-Speech**: Google Cloud TTS ➔ Azure TTS ↔ gTTS.
  - **Asset Fetching**: AI Image Generation (Hugging Face Stable Diffusion) ➔ Unsplash API ➔ Pexels / Pixabay APIs.
  - **Parallel Rendering**: Multi-process/parallel clip composition ➔ Sequential rendering ➔ Emergency flat copying if system resource thresholds are exceeded.
- **Premium Video Effects**:
  - Auto-scrolled dynamic word-by-word text layouts.
  - Smooth custom crossfades and audio fades.
  - Edge blur and background-blur matching filters for a polished look.
- **Full Automation Workflow**: Automatic thumbnail creation, localized file cleanup, and optional YouTube publication via OAuth integration.

---

## 📂 Project Structure

```
VideoOps/
├── automation/               # Core automation modules
│   ├── shorts_maker_I.py    # Image-based shorts creator (Even days)
│   ├── shorts_maker_V.py    # Video-based shorts creator (Odd days)
│   ├── parallel_renderer.py # Parallel multi-process video rendering
│   ├── parallel_tasks.py    # Concurrent rendering task management
│   ├── thumbnail.py         # Automated YouTube thumbnail generation
│   ├── voiceover.py         # TTS orchestration & Google Cloud implementation
│   ├── voiceover_azure.py   # Azure TTS implementation fallback
│   ├── youtube_auth.py      # OAuth2 authentication logic for YouTube API
│   ├── youtube_upload.py    # YouTube Data API upload integration
│   └── content_generator.py # Gemini-powered script & prompt generation
├── helper/                  # Modular auxiliary utilities
│   ├── image.py            # Image transformation (zoom, crop, watermarks)
│   ├── fetch.py            # API-based media downloads (Pexels, Pixabay, HF, Unsplash)
│   ├── crossfade.py        # Custom transitions and multi-clip fades
│   ├── text.py             # Complex word-by-word text-clip animation
│   ├── audio.py            # Audio processing, mixing, and timing
│   ├── memory.py           # System memory and CPU usage guardrails
│   ├── process.py          # Process-level resource monitoring
│   ├── minor_helper.py     # Cleanups, folder verification, file parsing
│   └── blur.py             # Advanced Gaussian/edge-blur visual utilities
├── packages/                # Shared package assets
│   └── fonts/
│       └── default_font.ttf # Consolidated project font
├── main.py                 # Primary orchestration entrypoint
├── requirements.txt         # Tailored python dependencies
├── run.sh                  # Automation cron runner with automatic git commits
└── _verify_keys.py         # Environment key diagnostics
```

---

## 🚀 Setup & Installation

### 1. Pre-requisites
Ensure you have the following system dependencies installed:
- **Python 3.10+**
- **FFmpeg**: Required for MoviePy video processing (`sudo apt install ffmpeg`)
- **ImageMagick**: Required for text effects and MoviePy text rendering (`sudo apt install imagemagick`)

### 2. Environment Setup
Clone the repository and prepare your virtual environment:
```sh
git clone https://github.com/yourusername/videoops.git
cd videoops

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install stripped down, fast dependencies
pip install -r requirements.txt
```

### 3. API Credentials Configuration
Create a `.env` file in the root directory. Paste and configure the following variables:

```env
# Google Cloud Platform
GCP_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/lazycreator-1.json

# LLM Config
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash-lite

# Stock Media & API Keys
PEXELS_API_KEY=your_pexels_api_key
PIXABAY_API_KEY=your_pixabay_api_key
NEWS_API_KEY=your_news_api_key
HF_API_TOKEN=your_huggingface_token

# Fallback Speech Keys (Optional, falls back to gTTS)
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=your_azure_speech_region

# Video Pipeline Configuration
ENABLE_YOUTUBE_UPLOAD=false
YOUTUBE_TOPIC="Artificial Intelligence"
DEBUG_MODE=false
```

---

## 🎮 Usage Guide

| Execution Command | Action |
| :--- | :--- |
| `python main.py` | Runs pipeline. Selects image or video creator automatically based on day-of-year parity. |
| `python main.py video` | Forces the video-based pipeline (`YTShortsCreator_V`) regardless of the day. |
| `python main.py image` | Forces the image-based pipeline (`YTShortsCreator_I`) regardless of the day. |
| `./run.sh` | Orchestrates a cron execution (auto-commits workspace files and runs the pipeline). |
| `DEBUG_MODE=true python main.py` | Runs with full verbose logging (`DEBUG` level) activated. |
| `python _verify_keys.py` | Diagnostics script to check and verify your API keys and service integrations. |

---

## 📄 License
This project is licensed under the MIT License.

