# ==============================================================================
# VideoOps 1.0 — Pipeline & Creative Configuration (config.yaml)
# ==============================================================================
# Created via `vops init`. Edit these settings to configure script generation,
# visual composition, captions, audio, and YouTube publishing.

# ------------------------------------------------------------------------------
# 1. Topic & Script Generation Settings
# ------------------------------------------------------------------------------
script:
  default_topic: "Artificial Intelligence"
  target_duration_seconds: 30       # Target overall speech duration in seconds
  cards_count: 5                    # Number of script segments (range: 3 to 8)
  tone: "fast_paced_breakdown"      # Options: fast_paced_breakdown, educational, authoritative, controversial, humorous
  target_audience: "software_engineers" # Options: software_engineers, tech_enthusiasts, general_audience
  hook_style: "bold_question"        # Options: bold_question, surprising_fact, common_mistake, provocative_claim
  cta_style: "subscribe_for_more"    # Options: subscribe_for_more, leave_comment, share_video, none
  language: "English"

# ------------------------------------------------------------------------------
# 2. Text Captions & Subtitles
# ------------------------------------------------------------------------------
captions:
  enabled: true                     # Toggle captions on/off (true/false)
  style: "pill"                     # Caption style: pill, none
  font_name: "Poppins-Black.ttf"
  font_size: 54

# ------------------------------------------------------------------------------
# 3. Audio & Voiceover (TTS) Synthesis
# ------------------------------------------------------------------------------
audio:
  provider: "edge"                  # Options: edge, supertonic, gtts
  edge_voice: "en-US-ChristopherNeural"

# ------------------------------------------------------------------------------
# 4. Visual Assets & Stock Media
# ------------------------------------------------------------------------------
visuals:
  primary_source: "pexels"          # Options: pexels, pixabay, unsplash, huggingface
  min_video_duration: 5.0           # Minimum duration for fetched stock clips

# ------------------------------------------------------------------------------
# 5. Media Compositor & Video Rendering
# ------------------------------------------------------------------------------
rendering:
  resolution:
    width: 1080
    height: 1920
  fps: 30
  crossfade_duration: 0.35          # Inter-clip crossfade transition in seconds
  ken_burns:
    enabled: true
    zoom_scale: 1.25                # Alternating zoom ratio (1.0 -> 1.25)

# ------------------------------------------------------------------------------
# 6. Publishing & YouTube Upload
# ------------------------------------------------------------------------------
publishing:
  youtube:
    enabled: false
    privacy_status: "private"        # Options: private, unlisted, public
    category_id: "28"                # 28 = Science & Technology
