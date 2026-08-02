"""Dedicated Font Utility Manager for loading, caching, and fallback management of TTF fonts."""

import logging
from pathlib import Path
from PIL import ImageFont

logger = logging.getLogger(__name__)

FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


class FontManager:
    """Manages custom TTF fonts and system fallbacks for high-contrast video overlays."""

    _cached_fonts: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

    @classmethod
    def get_font(
        cls,
        font_size: int = 48,
        font_name: str = "Montserrat-Bold.ttf",
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Load TTF font with fallback chain (Custom Local TTF -> System TTF -> PIL Default)."""
        cache_key = (font_name, font_size)
        if cache_key in cls._cached_fonts:
            return cls._cached_fonts[cache_key]

        # 1. Local font directory check
        candidate_paths = [
            FONTS_DIR / font_name,
            FONTS_DIR / "Montserrat-Bold.ttf",
            FONTS_DIR / "Inter-Bold.ttf",
            FONTS_DIR / "Anton-Regular.ttf",
        ]

        # 2. System font fallbacks
        candidate_paths.extend([
            Path("/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        ])

        for path in candidate_paths:
            if path.exists() and path.stat().st_size > 1024:
                try:
                    font = ImageFont.truetype(str(path), font_size)
                    cls._cached_fonts[cache_key] = font
                    logger.debug(f"Loaded font '{path.name}' at size {font_size}px")
                    return font
                except Exception as e:
                    logger.warning(f"Failed to load font '{path}': {e}")

        logger.warning(f"No custom TTF font found. Using default PIL font at size {font_size}px")
        font = ImageFont.load_default()
        cls._cached_fonts[cache_key] = font
        return font
