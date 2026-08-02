"""YouTube API non-interactive uploader service."""

import logging
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from videoops.config import settings

logger = logging.getLogger(__name__)


class YouTubePublisher:
    """Handles non-interactive OAuth YouTube video publishing."""

    def __init__(self) -> None:
        self.enabled = settings.ENABLE_YOUTUBE_UPLOAD

    def publish(self, video_path: str, title: str, description: str, thumbnail_path: str | None = None) -> str | None:
        """Publish video to YouTube if ENABLE_YOUTUBE_UPLOAD is True."""
        if not self.enabled:
            logger.info("YouTube upload disabled in config (ENABLE_YOUTUBE_UPLOAD=false). Skipping upload.")
            return None

        logger.info(f"Publishing video '{title}' to YouTube...")
        creds = Credentials(
            token=os.getenv("YOUTUBE_ACCESS_TOKEN"),
            refresh_token=os.getenv("YOUTUBE_REFRESH_TOKEN"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("YOUTUBE_CLIENT_ID"),
            client_secret=os.getenv("YOUTUBE_CLIENT_SECRET"),
        )

        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": title[:100],
                "description": description,
                "tags": ["Shorts", "AI", "Tech"],
                "categoryId": "28",  # Science & Technology
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()

        video_id = response.get("id")
        logger.info(f"Successfully uploaded video to YouTube! Video ID: {video_id}")

        if thumbnail_path and video_id:
            try:
                youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail_path)).execute()
                logger.info("Successfully set custom video thumbnail")
            except Exception as e:
                logger.warning(f"Failed to upload thumbnail: {e}")

        return video_id
