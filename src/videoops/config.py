"""Centralized configuration loader for videoops using Pydantic Settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings parsed from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Settings (OpenAI-compatible / NVIDIA API)
    LLM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_API_KEY: str | None = None
    LLM_API_KEY: str | None = None
    LLM_MODEL: str = "meta/llama-3.1-8b-instruct"

    # News & Media API Keys
    NEWS_API_KEY: str | None = None
    PEXELS_API_KEY: str | None = None
    PIXABAY_API_KEY: str | None = None
    HUGGINGFACE_API_KEY: str | None = None

    # TTS Settings
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    AZURE_SPEECH_KEY: str | None = None
    AZURE_SPEECH_REGION: str | None = None

    # YouTube Pipeline
    YOUTUBE_TOPIC: str = "Artificial Intelligence"
    ENABLE_YOUTUBE_UPLOAD: bool = False

    # Directories
    OUTPUT_DIR: str = "sandbox/outputs"
    TEMP_DIR: str = "sandbox/temp"

    @property
    def api_key(self) -> str:
        """Resolve LLM API key, prioritizing NVIDIA_API_KEY then LLM_API_KEY."""
        key = self.NVIDIA_API_KEY or self.LLM_API_KEY
        if not key:
            raise ValueError(
                "Missing LLM API key. Please set NVIDIA_API_KEY or LLM_API_KEY in your .env file."
            )
        return key

    @property
    def project_root(self) -> Path:
        """Root directory of the videoops repository."""
        return Path(__file__).resolve().parent.parent.parent

    @property
    def resolved_output_dir(self) -> Path:
        """Resolved Path for output directory inside codebase."""
        path = self.project_root / self.OUTPUT_DIR if not Path(self.OUTPUT_DIR).is_absolute() else Path(self.OUTPUT_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def resolved_temp_dir(self) -> Path:
        """Resolved Path for temporary directory inside codebase."""
        path = self.project_root / self.TEMP_DIR if not Path(self.TEMP_DIR).is_absolute() else Path(self.TEMP_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


# Singleton configuration instance
settings = Settings()
