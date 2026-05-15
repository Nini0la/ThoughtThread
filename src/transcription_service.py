from __future__ import annotations

from pathlib import Path

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

from src.config import Settings


class TranscriptionService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: AzureOpenAI | None = None

    def transcribe(self, audio_path: str | Path) -> str:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file does not exist: {path}")
        client = self._get_client()
        try:
            with path.open("rb") as audio_file:
                result = client.audio.transcriptions.create(
                    model=self.settings.whisper_deployment_name,
                    file=audio_file,
                )
        except Exception as exc:
            raise RuntimeError(f"Transcription failed: {exc}") from exc
        return (getattr(result, "text", "") or "").strip()

    def _get_client(self) -> AzureOpenAI:
        if self._client is not None:
            return self._client
        if not self.settings.azure_openai_endpoint:
            raise RuntimeError("AZURE_OPENAI_ENDPOINT is required for transcription")

        if self.settings.azure_openai_api_key:
            self._client = AzureOpenAI(
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_key=self.settings.azure_openai_api_key,
                api_version=self.settings.azure_openai_api_version,
            )
            return self._client

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default",
        )
        self._client = AzureOpenAI(
            azure_endpoint=self.settings.azure_openai_endpoint,
            azure_ad_token_provider=token_provider,
            api_version=self.settings.azure_openai_api_version,
        )
        return self._client

