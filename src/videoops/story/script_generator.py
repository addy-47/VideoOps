"""Script generation and visual query extraction using decoupled LLM calls and keyword algorithms."""

import logging
from videoops.config import settings
from videoops.domain.models import ContentPackage, ScriptCard, VoiceStyle
from videoops.story.client import StoryLLMClient
from videoops.story.keyword_extractor import extract_segment_keywords

logger = logging.getLogger(__name__)


def generate_comprehensive_content(topic: str) -> ContentPackage:
    """Generate a clean YouTube Short script package (title, description, narrative cards) via LLM."""
    cfg = settings.script_config
    llm = StoryLLMClient()

    cards_count = cfg.get("cards_count", 5)
    target_duration = cfg.get("target_duration_seconds", 30)
    tone = cfg.get("tone", "fast_paced_breakdown")
    target_audience = cfg.get("target_audience", "software_engineers")
    hook_style = cfg.get("hook_style", "bold_question")
    cta_style = cfg.get("cta_style", "subscribe_for_more")
    language = cfg.get("language", "English")

    prompt = f"""
    Create a high-retention vertical Short script package on the topic: "{topic}".

    Script Generation Parameters:
    - Target Duration: ~{target_duration} seconds total across exactly {cards_count} storyboard cards.
    - Script Tone: {tone}
    - Target Audience: {target_audience}
    - Hook Style: {hook_style}
    - Closing Call to Action: {cta_style}
    - Language: {language}

    Structure:
    - Card 1: {hook_style} opening hook sentence to grab immediate attention (second 0).
    - Middle Cards: Concise technical setup, core facts, breakdown, and mind-bending implications.
    - Final Card: Punchy closing statement with CTA ({cta_style}).

    Return ONLY a JSON object with this exact structure:
    {{
      "title": "Catchy Short Title (3-6 words)",
      "description": "Engaging 2-sentence description with 4 relevant hashtags",
      "script_cards": [
        {{
          "text": "Card narration text...",
          "duration": 5.0,
          "voice_style": "excited"
        }}
      ]
    }}
    """

    data = llm.generate_json(
        prompt=prompt,
        system_prompt=(
            "You are a master YouTube Shorts director and storyteller. You create tight, energetic, "
            "and informative vertical scripts engineered for maximum viewer retention with zero fluff."
        ),
    )

    if not isinstance(data, dict):
        raise ValueError(f"LLM returned invalid response type: {type(data)}")

    cards = []
    raw_cards = data.get("script_cards") or []

    for idx, raw_card in enumerate(raw_cards):
        text = raw_card.get("text", "").strip()
        dur = float(raw_card.get("duration", target_duration / max(1, len(raw_cards))))
        style_str = raw_card.get("voice_style", cfg.get("default_voice_style", "excited")).lower()

        try:
            v_style = VoiceStyle(style_str)
        except ValueError:
            v_style = VoiceStyle.EXCITED

        # Decoupled algorithmic visual keyword extraction for each card
        bg_query = extract_segment_keywords(text, topic=topic)

        cards.append(
            ScriptCard(
                text=text,
                duration=dur,
                voice_style=v_style,
                background_query=bg_query,
            )
        )

    title = data.get("title") or f"The Truth About {topic}"
    description = data.get("description") or f"Check out this breakdown of {topic}! #Shorts #{topic.replace(' ', '')}"

    return ContentPackage(
        title=title,
        description=description,
        script_cards=tuple(cards),
        thumbnail_hf_prompt=f"Photorealistic 8k portrait image depicting {topic}, cinematic lighting, 9:16 vertical",
        thumbnail_unsplash_query=extract_segment_keywords(title, topic=topic),
    )


def generate_batch_video_queries(
    section_texts: list[str],
    overall_topic: str
) -> dict[int, str]:
    """Generate visual stock video queries using fast algorithmic keyword extraction."""
    result = {}
    for idx, text in enumerate(section_texts):
        result[idx] = extract_segment_keywords(text, topic=overall_topic)
    return result


def generate_batch_image_prompts(
    section_texts: list[str],
    overall_topic: str
) -> dict[int, str]:
    """Generate AI image prompts using fast algorithmic keyword extraction."""
    result = {}
    for idx, text in enumerate(section_texts):
        kw = extract_segment_keywords(text, topic=overall_topic)
        result[idx] = f"Detailed 8k vertical image depicting {kw}, cinematic lighting, photorealistic"
    return result
