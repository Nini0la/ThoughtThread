from __future__ import annotations

import argparse
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

from src.audio_recorder import AudioRecorder
from src.classifier import Classifier
from src.config import Settings
from src.hotkey_listener import HotkeyListener
from src.memory_store import MemoryStore, NewMemoryEntry
from src.query_router import QueryRouter
from src.response_service import ResponseService
from src.transcription_service import TranscriptionService


class ThoughtThreadAssistant:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store
        self.classifier = Classifier()
        self.router = QueryRouter()
        self.responses = ResponseService(store)

    def handle_text(self, text: str) -> str:
        routed = self.router.route(text)
        if routed.intent == "retrieval":
            return self.ask(routed.cleaned_text)
        return self.capture(routed.cleaned_text)

    def capture(self, text: str) -> str:
        classified = self.classifier.classify(text)
        entry = self.store.add_entry(
            NewMemoryEntry(
                raw_transcript=text,
                cleaned_text=classified.cleaned_text,
                entry_type=classified.entry_type,
                due_at=classified.due_at,
                tags=classified.tags,
                metadata_json=classified.metadata_json,
            )
        )
        return f"Captured [{entry.entry_type}]: {entry.cleaned_text}"

    def ask(self, question: str) -> str:
        return self.responses.answer(question)


def build_assistant(settings: Settings | None = None) -> ThoughtThreadAssistant:
    settings = settings or Settings.from_env()
    return ThoughtThreadAssistant(MemoryStore(settings.memory_db_path))


def capture(text: str, db_path: str | Path | None = None) -> str:
    settings = Settings.from_env()
    if db_path is not None:
        settings = _settings_with_db(settings, Path(db_path))
    return build_assistant(settings).capture(text)


def ask(question: str, db_path: str | Path | None = None) -> str:
    settings = Settings.from_env()
    if db_path is not None:
        settings = _settings_with_db(settings, Path(db_path))
    return build_assistant(settings).ask(question)


def main() -> None:
    if load_dotenv:
        load_dotenv()
    parser = argparse.ArgumentParser(description="Transient memory voice assistant")
    subparsers = parser.add_subparsers(dest="command")

    capture_parser = subparsers.add_parser("capture", help="Capture text into memory")
    capture_parser.add_argument("text", nargs="+")

    ask_parser = subparsers.add_parser("ask", help="Ask a retrieval question")
    ask_parser.add_argument("question", nargs="+")

    handle_parser = subparsers.add_parser("text", help="Route text as capture or retrieval")
    handle_parser.add_argument("text", nargs="+")

    subparsers.add_parser("voice-once", help="Record once, transcribe, then route the transcript")
    subparsers.add_parser("listen", help="Run a background hotkey listener")

    args = parser.parse_args()
    settings = Settings.from_env()
    assistant = build_assistant(settings)

    if args.command == "capture":
        print(assistant.capture(" ".join(args.text)))
    elif args.command == "ask":
        print(assistant.ask(" ".join(args.question)))
    elif args.command == "text":
        print(assistant.handle_text(" ".join(args.text)))
    elif args.command == "voice-once":
        print(_capture_voice_once(settings, assistant))
    elif args.command == "listen":
        _listen(settings, assistant)
    else:
        parser.print_help()


def _capture_voice_once(settings: Settings, assistant: ThoughtThreadAssistant) -> str:
    recorder = AudioRecorder(settings)
    transcriber = TranscriptionService(settings)
    try:
        audio_path = recorder.record_to_wav()
        transcript = transcriber.transcribe(audio_path)
    except Exception as exc:
        return f"Voice capture failed: {exc}"
    finally:
        if "audio_path" in locals():
            audio_path.unlink(missing_ok=True)
    if not transcript:
        return "Voice capture produced no transcript."
    return assistant.handle_text(transcript)


def _listen(settings: Settings, assistant: ThoughtThreadAssistant) -> None:
    def on_activate() -> None:
        print(_capture_voice_once(settings, assistant))

    listener = HotkeyListener(settings.hotkey, on_activate)
    print(f"Listening for {settings.hotkey}. Press Ctrl-C to stop.")
    listener.start()
    try:
        listener.join()
    except KeyboardInterrupt:
        listener.stop()
        print("Stopped.")


def _settings_with_db(settings: Settings, db_path: Path) -> Settings:
    return Settings(
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_key=settings.azure_openai_api_key,
        azure_openai_api_version=settings.azure_openai_api_version,
        whisper_deployment_name=settings.whisper_deployment_name,
        gpt_deployment_name=settings.gpt_deployment_name,
        memory_db_path=db_path,
        hotkey=settings.hotkey,
        audio_sample_rate=settings.audio_sample_rate,
        audio_channels=settings.audio_channels,
        max_record_seconds=settings.max_record_seconds,
    )


if __name__ == "__main__":
    main()

