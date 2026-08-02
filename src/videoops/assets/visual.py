"""Visual Media Asset Provider (Stock Videos & AI/Stock Images)."""

import hashlib
import logging
from pathlib import Path
import requests
from videoops.config import settings
from videoops.domain.models import AssetType, MediaAsset

logger = logging.getLogger(__name__)


class VisualAssetProvider:
    """Acquires stock videos and AI/stock images with automated fallback chains."""

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or settings.resolved_temp_dir

    def _sanitize_query(self, query: str) -> str:
        """Clean script queries into targeted 2-3 word stock video search terms."""
        if not query:
            return "technology science"
        import re

        q_lower = query.lower()
        if "switch" in q_lower or "nintendo" in q_lower:
            return "nintendo switch"

        # Remove URLs, domain names, special characters
        q = re.sub(r"https?://\S+|- [a-zA-Z0-9.]+|\.com|\.org|\.net", "", query)
        q = re.sub(r"[^\w\s]", "", q).strip()

        # Stopwords to filter out
        stop_words = {
            "a", "an", "the", "in", "on", "at", "for", "to", "of", "and", "or", "is", "are",
            "this", "that", "it", "with", "by", "from", "about", "your", "you", "we", "how",
            "what", "why", "video", "query", "stock", "footage"
        }
        words = [w for w in q.split() if w.lower() not in stop_words]

        if not words:
            return "technology futuristic"

        # Limit to top 3 key words
        if len(words) > 3:
            words = words[:3]

        return " ".join(words).lower()

    def fetch_video(self, query: str, min_duration: float = 5.0) -> MediaAsset:
        """Fetch vertical stock video matching query (Pexels -> Pixabay)."""
        clean_q = self._sanitize_query(query)
        q_hash = hashlib.md5(clean_q.encode("utf-8")).hexdigest()[:8]
        clean_name = f"video_{q_hash}.mp4"
        output_path = self.output_dir / clean_name

        if output_path.exists() and output_path.stat().st_size > 10240:
            return MediaAsset(path=str(output_path), asset_type=AssetType.VIDEO, duration=min_duration)

        # 1. Try Pexels Video Search
        if settings.PEXELS_API_KEY:
            try:
                path = self._fetch_pexels_video(clean_q, output_path)
                if path:
                    logger.info(f"Fetched video from Pexels for query '{clean_q}'")
                    return MediaAsset(path=str(path), asset_type=AssetType.VIDEO, duration=min_duration)
            except Exception as e:
                logger.warning(f"Pexels video fetch failed: {e}")

        # 2. Try Pixabay Video API
        if settings.PIXABAY_API_KEY:
            try:
                path = self._fetch_pixabay_video(query, output_path)
                if path:
                    logger.info(f"Fetched video from Pixabay for query '{query}'")
                    return MediaAsset(path=str(path), asset_type=AssetType.VIDEO, duration=min_duration)
            except Exception as e:
                logger.warning(f"Pixabay video fetch failed: {e}")

        # 3. Fall back to image generation/fetching
        logger.info(f"Falling back to image asset for query '{query}'")
        return self.fetch_image(query)

    def fetch_image(self, query: str) -> MediaAsset:
        """Fetch or generate image matching query (HuggingFace -> Unsplash -> Pexels)."""
        import hashlib
        q_hash = hashlib.md5(query.encode("utf-8")).hexdigest()[:8]
        clean_name = f"image_{q_hash}.jpg"
        output_path = self.output_dir / clean_name

        # 1. Try HuggingFace FLUX / SD Inference
        if settings.HUGGINGFACE_API_KEY:
            try:
                path = self._generate_hf_image(query, output_path)
                if path:
                    logger.info(f"Generated AI image via HuggingFace for '{query[:30]}'")
                    return MediaAsset(path=str(path), asset_type=AssetType.IMAGE)
            except Exception as e:
                logger.warning(f"HuggingFace image generation failed: {e}")

        # 2. Try Unsplash / Pexels Image Search
        if settings.PEXELS_API_KEY:
            try:
                path = self._fetch_pexels_image(query, output_path)
                if path:
                    logger.info(f"Fetched stock image from Pexels for '{query}'")
                    return MediaAsset(path=str(path), asset_type=AssetType.IMAGE)
            except Exception as e:
                logger.warning(f"Pexels image search failed: {e}")

        # 3. Fallback solid color image
        path = self._create_fallback_image(output_path)
        return MediaAsset(path=str(path), asset_type=AssetType.IMAGE)

    def _fetch_pexels_video(self, query: str, output_path: Path) -> Path | None:
        headers = {"Authorization": settings.PEXELS_API_KEY}
        url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=3"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            videos = data.get("videos", [])
            if videos:
                files = videos[0].get("video_files", [])
                # Pick portrait HD link
                portrait_file = next((f for f in files if f.get("width", 0) < f.get("height", 1)), files[0])
                download_url = portrait_file.get("link")
                if download_url:
                    v_resp = requests.get(download_url, timeout=20)
                    with open(output_path, "wb") as f:
                        f.write(v_resp.content)
                    return output_path
        return None

    def _fetch_pixabay_video(self, query: str, output_path: Path) -> Path | None:
        url = f"https://pixabay.com/api/videos/?key={settings.PIXABAY_API_KEY}&q={query}&per_page=3"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            hits = resp.json().get("hits", [])
            if hits:
                v_data = hits[0].get("videos", {}).get("medium", {})
                download_url = v_data.get("url")
                if download_url:
                    v_resp = requests.get(download_url, timeout=20)
                    with open(output_path, "wb") as f:
                        f.write(v_resp.content)
                    return output_path
        return None

    def _generate_hf_image(self, prompt: str, output_path: Path) -> Path | None:
        headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
        url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        payload = {"inputs": prompt}
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200 and resp.content:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return output_path
        return None

    def _fetch_pexels_image(self, query: str, output_path: Path) -> Path | None:
        headers = {"Authorization": settings.PEXELS_API_KEY}
        url = f"https://api.pexels.com/v1/search?query={query}&orientation=portrait&per_page=3"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            photos = resp.json().get("photos", [])
            if photos:
                img_url = photos[0].get("src", {}).get("large2x") or photos[0].get("src", {}).get("original")
                if img_url:
                    img_resp = requests.get(img_url, timeout=15)
                    with open(output_path, "wb") as f:
                        f.write(img_resp.content)
                    return output_path
        return None

    def _create_fallback_image(self, output_path: Path) -> Path:
        from PIL import Image
        img = Image.new("RGB", (1080, 1920), color=(24, 28, 48))
        img.save(output_path)
        return output_path
