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

    _user_config: dict | None = None

    def get_user_config(self) -> dict:
        """Lazy load and parse config.yaml from project root or working directory."""
        if self._user_config is not None:
            return self._user_config

        import yaml
        config_file = Path.cwd() / "config.yaml"
        if not config_file.exists():
            config_file = self.project_root / "config.yaml"

        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    self._user_config = yaml.safe_load(f) or {}
                    return self._user_config
            except Exception:
                pass

        self._user_config = {}
        return self._user_config

    @property
    def script_config(self) -> dict:
        """Script generation configuration dictionary."""
        cfg = self.get_user_config().get("script", {})
        return {
            "default_topic": cfg.get("default_topic", self.YOUTUBE_TOPIC),
            "target_duration_seconds": cfg.get("target_duration_seconds", 30),
            "cards_count": cfg.get("cards_count", 5),
            "tone": cfg.get("tone", "fast_paced_breakdown"),
            "target_audience": cfg.get("target_audience", "software_engineers"),
            "hook_style": cfg.get("hook_style", "bold_question"),
            "cta_style": cfg.get("cta_style", "subscribe_for_more"),
            "language": cfg.get("language", "English"),
        }

    @property
    def captions_enabled(self) -> bool:
        """Check if caption overlays are enabled."""
        cfg = self.get_user_config().get("captions", {})
        return cfg.get("enabled", True)

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

