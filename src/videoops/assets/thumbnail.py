"""Thumbnail Generation Engine."""

import logging
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from videoops.assets.visual import VisualAssetProvider
from videoops.config import settings
from videoops.media.font_utils import FontManager

logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    """Creates eye-catching YouTube Shorts thumbnails with styled title overlays."""

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or settings.resolved_output_dir
        self.provider = VisualAssetProvider(self.output_dir)

    def generate(self, title: str, prompt: str | None = None) -> str:
        """Generate thumbnail image for short with high-contrast styled rounded pill title card."""
        query = prompt or title
        asset = self.provider.fetch_image(query)

        output_filename = self.output_dir / f"thumbnail_{hash(title) & 0xFFFFFFFF}.jpg"
        with Image.open(asset.path) as img:
            base_img = img.resize((1080, 1920)).convert("RGBA")
            overlay_layer = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay_layer)

            font = FontManager.get_font(font_size=54, font_name="Montserrat-Bold.ttf")

            # Max 3 words on thumbnail title badge for high impact
            title_words = [w.strip(":,!?.-—\"'()") for w in title.split()[:3]]
            title_words = [w for w in title_words if w]
            short_title = " ".join(title_words)

            center_x = 1080 // 2
            center_y = 1920 // 2

            # Measure exact full string rendered width using Pillow's official draw.textlength
            full_text_w = draw.textlength(short_title, font=font)
            text_bbox = draw.textbbox((0, 0), short_title, font=font)
            text_h = text_bbox[3] - text_bbox[1]

            # Massive 880px minimum width pill capsule so padding is always huge and symmetric
            card_h = max(76, text_h + 38)
            card_w = min(1040, max(880, int(full_text_w) + 400))

            left = center_x - card_w // 2
            top = center_y - card_h // 2
            right = left + card_w
            bottom = top + card_h

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
            last_w_i = len(title_words) - 1 if title_words else -1

            for w_i, word in enumerate(title_words):
                prefix = " ".join(title_words[:w_i]) + (" " if w_i > 0 else "")
                word_x = start_x + (draw.textlength(prefix, font=font) if prefix else 0)

                if w_i == last_w_i:
                    draw.text((word_x, center_y), word, fill=(255, 235, 20), font=font, anchor="lm", stroke_width=2, stroke_fill=(0, 0, 0))
                else:
                    draw.text((word_x, center_y), word, fill=(255, 255, 255), font=font, anchor="lm", stroke_width=2, stroke_fill=(0, 0, 0, 180))

            # Composite overlay onto base image and save as JPEG
            final_img = Image.alpha_composite(base_img, overlay_layer).convert("RGB")
            final_img.save(output_filename, "JPEG", quality=95)
            logger.info(f"Thumbnail created at {output_filename}")
            return str(output_filename)

        logger.info(f"Thumbnail created at {output_filename}")
        return str(output_filename)
