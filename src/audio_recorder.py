from __future__ import annotations

from pathlib import Path
import tempfile
import wave

import sounddevice as sd

from src.config import Settings


class AudioRecorder:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def record_to_wav(self, seconds: int | None = None) -> Path:
        duration = seconds or self.settings.max_record_seconds
        if duration <= 0:
            raise ValueError("Recording duration must be positive")

        try:
            audio = sd.rec(
                int(duration * self.settings.audio_sample_rate),
                samplerate=self.settings.audio_sample_rate,
                channels=self.settings.audio_channels,
                dtype="int16",
            )
            sd.wait()
        except Exception as exc:
            raise RuntimeError(f"Could not record audio: {exc}") from exc

        temp_file = tempfile.NamedTemporaryFile(prefix="thoughtthread-", suffix=".wav", delete=False)
        path = Path(temp_file.name)
        temp_file.close()
        try:
            with wave.open(str(path), "wb") as wav:
                wav.setnchannels(self.settings.audio_channels)
                wav.setsampwidth(2)
                wav.setframerate(self.settings.audio_sample_rate)
                wav.writeframes(audio.tobytes())
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return path
