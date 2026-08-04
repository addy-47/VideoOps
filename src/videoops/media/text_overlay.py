"""Pillow-based pill badge caption overlay builder (1-3 words centered)."""

import textwrap
from pathlib import Path
from PIL import Image, ImageDraw
from videoops.media.font_utils import FontManager

# Explicit Code Constants
DEFAULT_FONT_SIZE = 54
DEFAULT_FONT_NAME = "Poppins-Black.ttf"
DEFAULT_TEXT_COLOR = (255, 255, 255)
PILL_FILL_COLOR = (10, 12, 22, 210)
PILL_BORDER_COLOR = (255, 255, 255, 140)
TEXT_ACTIVE_COLOR = (255, 235, 20)
TEXT_NORMAL_COLOR = (255, 255, 255)
TEXT_STROKE_COLOR = (0, 0, 0)
TEXT_STROKE_WIDTH = 3
WORDS_PER_CHUNK = 3


class TextOverlayBuilder:
    """Builds sleek 1-3 word pill capsule overlays centered in the middle."""

    @staticmethod
    def create_text_image(
        text: str,
        output_path: Path,
        size: tuple[int, int] = (1080, 1920),
        font_size: int = DEFAULT_FONT_SIZE,
        font_name: str = DEFAULT_FONT_NAME,
        text_color: tuple[int, int, int] = DEFAULT_TEXT_COLOR,
        active_word_idx: int | None = None,
    ) -> Path:
        """Create sleek translucent pill badge centered in the middle (y = 960)."""
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        words = text.split()
        if not words:
            img.save(output_path, "PNG")
            return output_path

        # Clean trailing and leading punctuation/hyphens while preserving internal contraction apostrophes
        raw_words = words[:WORDS_PER_CHUNK] if words else []
        display_words = [w.strip(":,!?.-—\"'()") for w in raw_words]
        display_words = [w for w in display_words if w]

        if not display_words:
            img.save(output_path, "PNG")
            return output_path

        display_text = " ".join(display_words)
        char_count = len(display_text)
        if char_count > 22:
            font_sz = 42
        elif char_count > 16:
            font_sz = 48
        else:
            font_sz = font_size

        font = FontManager.get_font(font_size=font_sz, font_name=font_name)

        center_x = size[0] // 2
        center_y = size[1] // 2  # Dead center vertical alignment

        # Measure exact full string rendered width using Pillow's official draw.textlength
        full_text_w = draw.textlength(display_text, font=font)
        text_bbox = draw.textbbox((0, 0), display_text, font=font)
        text_h = text_bbox[3] - text_bbox[1]

        # Dynamic tight-fitting pill capsule
        card_h = max(90, text_h + 36)
        card_w = min(1000, max(240, int(full_text_w) + 70))

        left = center_x - card_w // 2
        top = center_y - card_h // 2
        right = left + card_w
        bottom = top + card_h

        pill_radius = card_h // 2

        # Draw pill capsule
        draw.rounded_rectangle(
            [(left, top), (right, bottom)],
            radius=pill_radius,
            fill=PILL_FILL_COLOR,
            outline=PILL_BORDER_COLOR,
            width=2,
        )

        # Centered bold typography rendering with stroke
        start_x = center_x - (full_text_w / 2)
        active_idx = active_word_idx % len(display_words) if (active_word_idx is not None and len(display_words) > 0) else -1

        for w_i, word in enumerate(display_words):
            prefix = " ".join(display_words[:w_i]) + (" " if w_i > 0 else "")
            word_x = start_x + (draw.textlength(prefix, font=font) if prefix else 0)

            if w_i == active_idx:
                draw.text(
                    (word_x, center_y),
                    word,
                    fill=TEXT_ACTIVE_COLOR,
                    font=font,
                    anchor="lm",
                    stroke_width=TEXT_STROKE_WIDTH,
                    stroke_fill=TEXT_STROKE_COLOR,
                )
            else:
                draw.text(
                    (word_x, center_y),
                    word,
                    fill=text_color,
                    font=font,
                    anchor="lm",
                    stroke_width=TEXT_STROKE_WIDTH,
                    stroke_fill=(0, 0, 0, 200),
                )

        img.save(output_path, "PNG")
        return output_path
