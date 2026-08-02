"""Script generation and batch query generator using OpenAI-compatible LLM client."""

import logging
from videoops.domain.models import ContentPackage, ScriptCard
from videoops.story.client import StoryLLMClient

logger = logging.getLogger(__name__)


def generate_comprehensive_content(topic: str) -> ContentPackage:
    """Generate a full YouTube Short package (title, description, script cards, thumbnail prompts)."""
    llm = StoryLLMClient()

    prompt = f"""
    Create a top-tier, highly engaging YouTube Short script package on the topic: "{topic}".
    The video must have 5 to 7 storyboard cards (~25-35 seconds total speech duration) following a high-retention viral arc:
    1. Card 1 (Hook): An attention-grabbing hook or controversial question.
    2. Card 2 (Setup): Concise background or why this topic matters right now.
    3. Card 3 (Core Fact 1): A fascinating main fact, breakdown, or discovery.
    4. Card 4 (Core Fact 2): Deepening detail or supporting evidence.
    5. Card 5 (Twist/Mind-Bender): An unexpected reveal, plot twist, or key implication.
    6. Card 6 (Conclusion/CTA): Strong closing line or call to action.

    CRITICAL: For every card, "background_query" MUST be a highly specific 2-3 word stock video search term directly matching that card's sentence (e.g., if topic is AI robotics and card mentions server rooms, use "server room lights"; if card mentions human cyborg, use "cybernetic human").

    Return ONLY a JSON object with this exact structure:
    {{
      "title": "Short Catchy YouTube Title (3-6 words)",
      "description": "Engaging 2-sentence description with 4 relevant hashtags",
      "script_cards": [
        {{
          "text": "Hook sentence grabbing immediate interest...",
          "duration": 4.5,
          "voice_style": "excited",
          "background_query": "specific video search query for card 1"
        }},
        ...
      ],
      "thumbnail_hf_prompt": "Photorealistic 8k portrait matching topic...",
      "thumbnail_unsplash_query": "specific topic search query"
    }}
    """

    data = llm.generate_json(
        prompt=prompt,
        system_prompt=(
            "You are a master YouTube Shorts director and storyteller. You create tight, energetic, "
            "and informative scripts that hold viewer attention from second 0 to the end with zero fluff or AI slop."
        )
    )

    if not isinstance(data, dict):
        raise ValueError(f"LLM returned invalid response type: {type(data)}")

    from videoops.domain.models import VoiceStyle
    cards = []
    raw_cards = data.get("script_cards") or []
    for raw_card in raw_cards:
        style_str = raw_card.get("voice_style", "excited").lower()
        try:
            v_style = VoiceStyle(style_str)
        except ValueError:
            v_style = VoiceStyle.EXCITED

        cards.append(
            ScriptCard(
                text=raw_card.get("text", ""),
                duration=float(raw_card.get("duration", 4.0)),
                voice_style=v_style,
                background_query=raw_card.get("background_query"),
            )
        )

    return ContentPackage(
        title=data.get("title") or f"The Future of {topic}",
        description=data.get("description") or f"Check out this short about {topic}! #Shorts #{topic.replace(' ', '')}",
        script_cards=tuple(cards),
        thumbnail_hf_prompt=data.get("thumbnail_hf_prompt"),
        thumbnail_unsplash_query=data.get("thumbnail_unsplash_query"),
    )


def generate_batch_video_queries(
    section_texts: list[str],
    overall_topic: str
) -> dict[int, str]:
    """Generate stock video search queries for each section text."""
    llm = StoryLLMClient()

    prompt = f"""
    Overall Topic: "{overall_topic}"

    For each section text below, generate a 2-4 word stock video search query (for Pexels/Pixabay):
    {section_texts}

    Return a JSON object mapping index to search query, e.g.:
    {{
      "0": "futuristic robot AI",
      "1": "server room lights"
    }}
    """

    data = llm.generate_json(prompt=prompt)
    return {int(k): str(v) for k, v in data.items() if str(k).isdigit()}


def generate_batch_image_prompts(
    section_texts: list[str],
    overall_topic: str
) -> dict[int, str]:
    """Generate AI image prompts for each section text."""
    llm = StoryLLMClient()

    prompt = f"""
    Overall Topic: "{overall_topic}"

    For each section text below, generate a detailed image prompt (for HuggingFace SD/FLUX):
    {section_texts}

    Return a JSON object mapping index to image prompt, e.g.:
    {{
      "0": "Cyberpunk hacker working on holographic displays, photorealistic 8k",
      "1": "Quantum supercomputer core with glowing blue lights"
    }}
    """

    data = llm.generate_json(prompt=prompt)
    return {int(k): str(v) for k, v in data.items() if str(k).isdigit()}
