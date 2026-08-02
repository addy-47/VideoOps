"""Supertonic-3 ONNX Runtime TTS provider for local offline high-quality speech synthesis."""

import hashlib
import logging
import subprocess
from pathlib import Path
import numpy as np
import onnxruntime as ort
import soundfile as sf

from videoops.config import settings
from videoops.domain.models import AssetType, MediaAsset

logger = logging.getLogger(__name__)

SUPERTONIC_MODEL_DIR = Path(__file__).resolve().parent.parent.parent.parent / "sandbox" / "models" / "tts" / "supertonic-3"


import threading

_init_lock = threading.Lock()

class TTSProvider:
    """Local Supertonic-3 ONNX Runtime speech synthesizer with FFmpeg speech acceleration."""

    _te_session: ort.InferenceSession | None = None
    _dp_session: ort.InferenceSession | None = None
    _ve_session: ort.InferenceSession | None = None
    _vc_session: ort.InferenceSession | None = None

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or settings.resolved_temp_dir
        self.model_dir = SUPERTONIC_MODEL_DIR
        if not self.model_dir.exists():
            # Fallback to system .vox model path
            self.model_dir = Path.home() / ".vox" / "models" / "tts" / "supertonic-3"

    @classmethod
    def _init_sessions(cls, model_dir: Path) -> None:
        """Initialize ONNX Runtime inference sessions lazily with thread safety."""
        with _init_lock:
            if cls._te_session is None:
                opts = ort.SessionOptions()
                opts.intra_op_num_threads = 2
                opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

                logger.info(f"Initializing Supertonic-3 ONNX TTS models from '{model_dir}'...")
                cls._te_session = ort.InferenceSession(str(model_dir / "text_encoder.int8.onnx"), opts)
                cls._dp_session = ort.InferenceSession(str(model_dir / "duration_predictor.int8.onnx"), opts)
                cls._ve_session = ort.InferenceSession(str(model_dir / "vector_estimator.int8.onnx"), opts)
                cls._vc_session = ort.InferenceSession(str(model_dir / "vocoder.int8.onnx"), opts)

    def synthesize(self, text: str, filename_prefix: str = "tts_") -> MediaAsset:
        """Synthesize text into speech WAV/MP3 file using Supertonic-3 ONNX Runtime."""
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
        raw_wav_name = f"{filename_prefix}_{text_hash}_raw.wav"
        final_mp3_name = f"{filename_prefix}_{text_hash}.mp3"

        raw_wav_path = self.output_dir / raw_wav_name
        final_mp3_path = self.output_dir / final_mp3_name

        if final_mp3_path.exists() and final_mp3_path.stat().st_size > 1024:
            logger.info(f"Using cached Supertonic TTS speech file: '{final_mp3_path.name}'")
            duration = self._get_audio_duration(final_mp3_path)
            return MediaAsset(path=str(final_mp3_path), asset_type=AssetType.AUDIO, duration=duration)

        self._init_sessions(self.model_dir)

        # 1. Text tokenization (unicode mapping)
        chars = [ord(c) for c in text]
        text_ids = np.array([chars], dtype=np.int64)
        text_len = len(chars)
        text_mask = np.ones((1, 1, text_len), dtype=np.float32)

        # Zero style latents
        style_ttl = np.zeros((1, 50, 256), dtype=np.float32)
        style_dp = np.zeros((1, 8, 16), dtype=np.float32)

        # 2. Text Encoder & Duration Predictor
        text_emb = self._te_session.run(None, {"text_ids": text_ids, "style_ttl": style_ttl, "text_mask": text_mask})[0]
        dur = self._dp_session.run(None, {"text_ids": text_ids, "style_dp": style_dp, "text_mask": text_mask})[0]

        latent_len = int(np.round(float(dur.flatten()[0]))) if dur.size > 0 else int(text_len * 1.5)
        latent_len = max(12, latent_len)

        # 3. Vector Estimator Flow Matching (5 steps)
        latent = np.random.randn(1, 144, latent_len).astype(np.float32)
        latent_mask = np.ones((1, 1, latent_len), dtype=np.float32)
        steps = 5

        for step in range(steps):
            c_step = np.array([step], dtype=np.float32)
            t_step = np.array([steps], dtype=np.float32)
            vel = self._ve_session.run(
                None,
                {
                    "noisy_latent": latent,
                    "text_emb": text_emb,
                    "style_ttl": style_ttl,
                    "latent_mask": latent_mask,
                    "text_mask": text_mask,
                    "current_step": c_step,
                    "total_step": t_step,
                },
            )[0]
            latent = latent + (1.0 / steps) * vel

        # 4. Vocoder waveform synthesis (44.1kHz)
        audio = self._vc_session.run(None, {"latent": latent})[0].squeeze()
        sf.write(str(raw_wav_path), audio, 44100)

        # 5. Apply 1.18x speech rate speedup via FFmpeg
        final_path = self._speedup_audio(raw_wav_path, final_mp3_path, speed_factor=1.18)
        duration = self._get_audio_duration(final_path)

        # Cleanup raw unaccelerated WAV file
        if raw_wav_path.exists():
            try:
                raw_wav_path.unlink()
            except Exception:
                pass

        logger.info(f"Synthesized Supertonic-3 ONNX speech audio ({duration:.2f}s) -> '{final_path.name}'")
        return MediaAsset(path=str(final_path), asset_type=AssetType.AUDIO, duration=duration)

    def _speedup_audio(self, input_path: Path, output_path: Path, speed_factor: float = 1.18) -> Path:
        """Accelerate speech pacing using FFmpeg atempo filter without changing pitch."""
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-filter:a",
            f"atempo={speed_factor}",
            "-vn",
            "-acodec",
            "libmp3lame",
            "-q:a",
            "2",
            str(output_path),
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return output_path
        except Exception as e:
            logger.warning(f"Audio speedup failed: {e}. Using raw WAV file.")
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
