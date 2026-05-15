# transient-memory-voice-assistant

A macOS-first assistant for short-term cognitive continuity. It captures thoughts, tasks, reminders, questions, and current context, then answers lightweight retrieval questions from recent local memory.

The core assistant is text-first. Voice capture is only an input layer that records audio, transcribes it, and passes the transcript through the same `capture(text)` / `ask(question)` pipeline.

## Status

Phase 1 text MVP is implemented:

- capture text into SQLite
- classify entries as `TASK`, `CONTEXT`, `REMINDER`, `QUESTION`, or `NOTE`
- retrieve by recency, keyword, entry type, and open/done status
- mark the most recent open task done

Phase 2 voice adapters are scaffolded:

- global hotkey listener
- microphone recording
- Azure OpenAI Whisper transcription
- transcript routing through the same text pipeline

## Setup

Install dependencies with `uv`:

```bash
uv sync --extra dev
```

Create local configuration:

```bash
cp .env.example .env
```

## Azure OpenAI Configuration

Set these values in `.env`:

```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-06-01
WHISPER_DEPLOYMENT_NAME=whisper
GPT_DEPLOYMENT_NAME=gpt-4o-mini
```

`AZURE_OPENAI_API_KEY` is optional if your local Azure identity has access to the Azure OpenAI resource. In that case, the app uses `DefaultAzureCredential`.

## macOS Permissions

Voice mode needs:

- Microphone permission for the terminal app you run from
- Accessibility permission for global hotkeys through `pynput`

Grant these in System Settings:

- Privacy & Security > Microphone
- Privacy & Security > Accessibility

## Run

Capture text:

```bash
uv run thoughtthread capture "I need to reply to Bola before 6"
```

Ask a retrieval question:

```bash
uv run thoughtthread ask "What was I doing?"
```

Let the router decide whether text is capture or retrieval:

```bash
uv run thoughtthread text "What did I say about email?"
```

Record once and route the transcript:

```bash
uv run thoughtthread voice-once
```

Run the hotkey listener:

```bash
uv run thoughtthread listen
```

The default hotkey is `Ctrl-Shift-Space`. Change it with:

```bash
HOTKEY="<cmd>+<shift>+space"
```

## Supported Queries

Examples:

- `What was I doing?`
- `What should I be doing?`
- `What was due?`
- `What did I say about email?`
- `Show recent tasks`
- `Mark last task done`

## Local Storage

SQLite is used for the MVP. By default the database is stored at:

```text
.thoughtthread/memory.sqlite3
```

The `entries` table contains:

- `id`
- `created_at`
- `raw_transcript`
- `cleaned_text`
- `entry_type`
- `status`
- `due_at`
- `tags`
- `metadata_json`

Status values are `open`, `done`, and `archived`.

## Tests

```bash
uv run pytest
```

The tests cover text capture, context retrieval, open task/reminder retrieval, keyword lookup, task completion, and confirmation that voice transcripts use the same routing pipeline as typed text.

## Future Features

- semantic search
- embeddings
- Apple Reminders integration
- Todoist/Notion integration
- menu bar UI
- spoken responses
- proactive nudging/check-ins
- transient context summarization

