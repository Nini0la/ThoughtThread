from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    azure_openai_endpoint: str | None
    azure_openai_api_key: str | None
    azure_openai_api_version: str
    whisper_deployment_name: str
    gpt_deployment_name: str
    memory_db_path: Path
    hotkey: str
    audio_sample_rate: int
    audio_channels: int
    max_record_seconds: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            azure_openai_endpoint=_optional_env("AZURE_OPENAI_ENDPOINT"),
            azure_openai_api_key=_optional_env("AZURE_OPENAI_API_KEY"),
            azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01"),
            whisper_deployment_name=os.getenv("WHISPER_DEPLOYMENT_NAME", "whisper"),
            gpt_deployment_name=os.getenv("GPT_DEPLOYMENT_NAME", "gpt-4o-mini"),
            memory_db_path=Path(os.getenv("MEMORY_DB_PATH", ".thoughtthread/memory.sqlite3")),
            hotkey=os.getenv("HOTKEY", "<ctrl>+<shift>+space"),
            audio_sample_rate=int(os.getenv("AUDIO_SAMPLE_RATE", "16000")),
            audio_channels=int(os.getenv("AUDIO_CHANNELS", "1")),
            max_record_seconds=int(os.getenv("MAX_RECORD_SECONDS", "30")),
        )

    @property
    def azure_configured(self) -> bool:
        return bool(self.azure_openai_endpoint and self.azure_openai_api_key)


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None

