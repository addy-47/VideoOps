"""Keyword and keyphrase extraction for visual asset queries using the YAKE NLP library."""

import logging
import yake

logger = logging.getLogger(__name__)

# Initialize YAKE KeywordExtractor for English 1-2 n-gram keyphrases
_kw_extractor = yake.KeywordExtractor(
    lan="en",
    n=2,               # Extract up to 2-word keyphrases (e.g., "container deployment")
    dedupLim=0.8,      # Deduplication threshold
    top=4,              # Return top 4 keyphrases
    features=None,
)


def extract_segment_keywords(text: str, topic: str | None = None, max_keywords: int = 3) -> str:
    """Extract keyphrases using YAKE statistical NLP keyphrase extractor.
    
    YAKE scores keyphrases by word frequency, position, casing, and context.
    Lower score = higher relevance in YAKE.
    """
    if not text or not text.strip():
        return topic or "technology"

    try:
        # Extract keywords (returns list of tuples: (kw, score))
        keywords_tuple = _kw_extractor.extract_keywords(text)
        
        # Sort by best (lowest YAKE score)
        sorted_kws = sorted(keywords_tuple, key=lambda x: x[1])
        selected_phrases = [kw for kw, _ in sorted_kws[:max_keywords]]

        if selected_phrases:
            query = " ".join(selected_phrases)
            if topic and topic.lower() not in query.lower():
                query = f"{topic} {query}".strip()
            return query
    except Exception as e:
        logger.warning(f"YAKE keyword extraction fallback for text '{text[:20]}...': {e}")

    return topic or "technology"
