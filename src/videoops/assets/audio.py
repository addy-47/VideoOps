"""Offline Supertonic-3 TTS (via sherpa-onnx) & Edge Neural TTS audio asset provider."""

import hashlib
import logging
import subprocess
import threading
from pathlib import Path

from videoops.config import settings
from videoops.domain.models import AssetType, MediaAsset

logger = logging.getLogger(__name__)

SUPERTONIC_MODEL_DIR = Path(__file__).resolve().parent.parent.parent.parent / "sandbox" / "models" / "tts" / "supertonic-3"
DEFAULT_AUDIO_FALLBACK_DURATION = 4.0
_init_lock = threading.Lock()



class TTSProvider:
    """TTS asset provider supporting sherpa-onnx Supertonic-3, Edge TTS, and fallback chains."""

    _sherpa_tts = None

    def __init__(self, output_dir: Path | None = None, mode: str = "edge") -> None:
        self.output_dir = output_dir or settings.resolved_temp_dir
        self.mode = mode
        self.model_dir = SUPERTONIC_MODEL_DIR
        if not self.model_dir.exists():
            self.model_dir = Path.home() / ".vox" / "models" / "tts" / "supertonic-3"

    @classmethod
    def _init_sherpa_onnx(cls, model_dir: Path):
        """Initialize sherpa-onnx Supertonic-3 OfflineTts engine with thread safety."""
        with _init_lock:
            if cls._sherpa_tts is None:
                import sherpa_onnx

                logger.info(f"Initializing sherpa-onnx Supertonic-3 engine from '{model_dir}'...")
                config = sherpa_onnx.OfflineTtsConfig(
                    model=sherpa_onnx.OfflineTtsModelConfig(
                        supertonic=sherpa_onnx.OfflineTtsSupertonicModelConfig(
                            text_encoder=str(model_dir / "text_encoder.int8.onnx"),
                            duration_predictor=str(model_dir / "duration_predictor.int8.onnx"),
                            vector_estimator=str(model_dir / "vector_estimator.int8.onnx"),
                            vocoder=str(model_dir / "vocoder.int8.onnx"),
                            tts_json=str(model_dir / "tts.json"),
                            unicode_indexer=str(model_dir / "unicode_indexer.bin"),
                            voice_style=str(model_dir / "voice.bin"),
                        )
                    )
                )
                cls._sherpa_tts = sherpa_onnx.OfflineTts(config)

    def synthesize(self, text: str, filename_prefix: str = "tts_") -> MediaAsset:
        """Synthesize text into speech MP3/WAV file with automated provider fallback."""
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
        final_mp3_name = f"{filename_prefix}_{text_hash}.mp3"
        final_mp3_path = self.output_dir / final_mp3_name

        if final_mp3_path.exists() and final_mp3_path.stat().st_size > 1024:
            logger.info(f"Using cached TTS speech file: '{final_mp3_path.name}'")
            duration = self._get_audio_duration(final_mp3_path)
            return MediaAsset(path=str(final_mp3_path), asset_type=AssetType.AUDIO, duration=duration)

        # Mode Selection: "edge" vs "supertonic"
        if self.mode == "supertonic":
            asset = self._synthesize_sherpa_supertonic(text, filename_prefix, text_hash)
            if asset:
                return asset
            logger.warning("Supertonic TTS failed. Falling back to Edge TTS...")

        # Edge Neural TTS Primary
        asset = self._synthesize_edge_tts(text, final_mp3_path)
        if asset:
            return asset

        # Fallback to sherpa-onnx Supertonic if edge-tts failed
        asset = self._synthesize_sherpa_supertonic(text, filename_prefix, text_hash)
        if asset:
            return asset

        # Final gTTS Fallback
        return self._synthesize_gtts(text, final_mp3_path)

    def _synthesize_edge_tts(self, text: str, output_path: Path) -> MediaAsset | None:
        """Synthesize via Edge Neural AI Voice."""
        try:
            import asyncio
            import edge_tts

            voice = "en-US-ChristopherNeural"
            logger.info(f"Synthesizing Neural TTS audio with Edge TTS ({voice}) for: '{text[:30]}...'")

            async def _synth():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(str(output_path))

            asyncio.run(_synth())

            if output_path.exists() and output_path.stat().st_size > 1024:
                duration = self._get_audio_duration(output_path)
                logger.info(f"Successfully synthesized Edge TTS audio ({duration:.2f}s) -> '{output_path.name}'")
                return MediaAsset(path=str(output_path), asset_type=AssetType.AUDIO, duration=duration)
        except Exception as e:
            logger.warning(f"Edge TTS synthesis failed: {e}")
        return None

    def _synthesize_sherpa_supertonic(self, text: str, prefix: str, text_hash: str) -> MediaAsset | None:
        """Synthesize via sherpa-onnx native Supertonic-3 engine."""
        try:
            import soundfile as sf

            self._init_sherpa_onnx(self.model_dir)
            logger.info(f"Synthesizing speech via sherpa-onnx Supertonic-3 for: '{text[:30]}...'")

            audio = self._sherpa_tts.generate(text, sid=0, speed=1.0)
            raw_wav_path = self.output_dir / f"{prefix}_{text_hash}_sherpa.wav"
            final_mp3_path = self.output_dir / f"{prefix}_{text_hash}.mp3"

            sf.write(str(raw_wav_path), audio.samples, audio.sample_rate)
            final_path = self._convert_wav_to_mp3(raw_wav_path, final_mp3_path)
            duration = self._get_audio_duration(final_path)

            if raw_wav_path.exists():
                try:
                    raw_wav_path.unlink()
                except Exception:
                    pass

            logger.info(f"Successfully synthesized sherpa-onnx Supertonic-3 audio ({duration:.2f}s) -> '{final_path.name}'")
            return MediaAsset(path=str(final_path), asset_type=AssetType.AUDIO, duration=duration)
        except Exception as e:
            logger.warning(f"sherpa-onnx Supertonic-3 synthesis failed: {e}")
        return None

    def _synthesize_gtts(self, text: str, output_path: Path) -> MediaAsset:
        """Fallback synthesis using gTTS."""
        from gtts import gTTS

        logger.info("Synthesizing fallback speech with gTTS...")
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(str(output_path))
        duration = self._get_audio_duration(output_path)
        return MediaAsset(path=str(output_path), asset_type=AssetType.AUDIO, duration=duration)

    def _convert_wav_to_mp3(self, input_path: Path, output_path: Path) -> Path:
        """Convert WAV audio to MP3 format via FFmpeg."""
        cmd = ["ffmpeg", "-y", "-i", str(input_path), "-vn", "-acodec", "libmp3lame", "-q:a", "2", str(output_path)]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return output_path
        except Exception:
            return input_path

    def _get_audio_duration(self, file_path: Path) -> float:
        """Probe audio file duration using ffprobe."""
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(file_path),
        ]
        try:
            res = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return float(res.stdout.strip())
        except Exception:
            return 4.0
