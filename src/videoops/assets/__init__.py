"""Asset Acquisition Engine (Layer 3)."""

from videoops.assets.audio import TTSProvider
from videoops.assets.visual import VisualAssetProvider
from videoops.assets.thumbnail import ThumbnailGenerator

__all__ = [
    "TTSProvider",
    "VisualAssetProvider",
    "ThumbnailGenerator",
]
