"""Pillow-based glassmorphism translucent pill badge caption overlay builder (1-3 words centered)."""

import textwrap
from pathlib import Path
from PIL import Image, ImageDraw
from videoops.media.font_utils import FontManager


class TextOverlayBuilder:
    """Builds sleek 1-3 word translucent glassmorphism pill capsule overlays centered dead in the middle."""

    @staticmethod
    def create_text_image(
        text: str,
        output_path: Path,
        size: tuple[int, int] = (1080, 1920),
        font_size: int = 54,
        font_name: str = "Montserrat-Bold.ttf",
        text_color: tuple[int, int, int] = (255, 255, 255),
        pill_color: tuple[int, int, int, int] = (0, 0, 0, 160),  # Translucent frosted dark pill
        accent_color: tuple[int, int, int, int] = (255, 255, 255, 60),  # Subtle translucent glass stroke
        active_word_idx: int | None = None,
    ) -> Path:
        """Create sleek glassmorphism translucent pill badge centered dead in the middle (y = 960)."""
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Load bold custom TTF font
        font = FontManager.get_font(font_size=font_size, font_name=font_name)

        words = text.split()
        if not words:
            img.save(output_path, "PNG")
            return output_path

        # Clean trailing and leading punctuation/hyphens while preserving internal contraction apostrophes
        raw_words = words[:3] if words else []
        display_words = [w.strip(":,!?.-—\"'()") for w in raw_words]
        display_words = [w for w in display_words if w]

        if not display_words:
            img.save(output_path, "PNG")
            return output_path

        display_text = " ".join(display_words)
        char_count = len(display_text)
        if char_count > 22:
            font_sz = 26
        elif char_count > 16:
            font_sz = 30
        elif char_count > 10:
            font_sz = 34
        else:
            font_sz = 40

        font = FontManager.get_font(font_size=font_sz, font_name=font_name)

        center_x = size[0] // 2
        center_y = size[1] // 2  # 960px dead center vertical alignment

        # Measure exact full string rendered width using Pillow's official draw.textlength
        full_text_w = draw.textlength(display_text, font=font)
        text_bbox = draw.textbbox((0, 0), display_text, font=font)
        text_h = text_bbox[3] - text_bbox[1]

        # Massive 880px minimum width pill capsule so padding is always huge and symmetric
        card_h = max(80, text_h + 40)
        card_w = min(1040, max(880, int(full_text_w) + 400))

        left = center_x - card_w // 2
        top = center_y - card_h // 2
        right = left + card_w
        bottom = top + card_h

        # Capsule radius = half height
        pill_radius = card_h // 2

        # Single ultra-clean translucent dark frosted glass pill capsule (crisp 1px border)
        draw.rounded_rectangle(
            [(left, top), (right, bottom)],
            radius=pill_radius,
            fill=(0, 0, 0, 180),
            outline=(255, 255, 255, 120),
            width=1,
        )

        # Mathematically exact dead-center positioning using Pillow's internal font engine metrics
        start_x = center_x - (full_text_w / 2)
        active_idx = active_word_idx % len(display_words) if (active_word_idx is not None and len(display_words) > 0) else -1

        for w_i, word in enumerate(display_words):
            prefix = " ".join(display_words[:w_i]) + (" " if w_i > 0 else "")
            word_x = start_x + (draw.textlength(prefix, font=font) if prefix else 0)

            if w_i == active_idx:
                draw.text((word_x, center_y), word, fill=(255, 235, 20), font=font, anchor="lm", stroke_width=2, stroke_fill=(0, 0, 0))
            else:
                draw.text((word_x, center_y), word, fill=(255, 255, 255), font=font, anchor="lm", stroke_width=2, stroke_fill=(0, 0, 0, 180))

        img.save(output_path, "PNG")
        return output_path
