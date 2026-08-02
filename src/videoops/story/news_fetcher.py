"""NewsAPI fetcher for daily topic selection."""

import logging
import requests
from videoops.config import settings

logger = logging.getLogger(__name__)


def get_latest_news() -> str:
    """Fetch top news headline from NewsAPI or fallback to default topic."""
    if not settings.NEWS_API_KEY:
        logger.info("NEWS_API_KEY not set. Using default topic.")
        return settings.YOUTUBE_TOPIC

    url = f"https://newsapi.org/v2/top-headlines?category=technology&language=en&pageSize=5&apiKey={settings.NEWS_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            if articles:
                headline = articles[0].get("title")
                if headline:
                    logger.info(f"Fetched headline from NewsAPI: {headline}")
                    return headline
    except Exception as e:
        logger.warning(f"Failed to fetch news from NewsAPI: {e}")

    return settings.YOUTUBE_TOPIC
