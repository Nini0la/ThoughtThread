from __future__ import annotations

from src.main import ThoughtThreadAssistant
from src.memory_store import MemoryStore
from src.query_router import QueryRouter


def make_assistant(tmp_path):
    return ThoughtThreadAssistant(MemoryStore(tmp_path / "memory.sqlite3"))


def test_user_can_create_tasks_and_context_entries_from_text(tmp_path):
    assistant = make_assistant(tmp_path)

    task_response = assistant.capture("I need to reply to Bola before 6")
    context_response = assistant.capture("I'm currently debugging Azure auth")

    assert "Captured [TASK]" in task_response
    assert "Captured [CONTEXT]" in context_response


def test_user_can_retrieve_recent_context(tmp_path):
    assistant = make_assistant(tmp_path)
    assistant.capture("I'm currently debugging Azure auth")

    answer = assistant.ask("What was I doing?")

    assert "debugging Azure auth" in answer


def test_user_can_retrieve_open_tasks_and_reminders(tmp_path):
    assistant = make_assistant(tmp_path)
    assistant.capture("I need to send that invoice tonight")
    assistant.capture("Need to check my email for the invoice")

    answer = assistant.ask("What should I be doing?")

    assert "send that invoice" in answer
    assert "check my email" in answer


def test_user_can_retrieve_due_items(tmp_path):
    assistant = make_assistant(tmp_path)
    assistant.capture("I need to send that invoice tonight")

    answer = assistant.ask("What was due?")

    assert "send that invoice" in answer
    assert "tonight" in answer


def test_user_can_query_for_past_mentions_of_keywords(tmp_path):
    assistant = make_assistant(tmp_path)
    assistant.capture("Need to check my email for the invoice")
    assistant.capture("I'm currently debugging Azure auth")

    answer = assistant.ask("What did I say about email?")

    assert "check my email" in answer
    assert "Azure auth" not in answer


def test_user_can_mark_tasks_done(tmp_path):
    assistant = make_assistant(tmp_path)
    assistant.capture("I need to send that invoice tonight")

    done_answer = assistant.ask("Mark last task done")
    task_answer = assistant.ask("Show recent tasks")

    assert "Marked done" in done_answer
    assert "do not see any open tasks" in task_answer


def test_voice_transcript_uses_same_routing_pipeline(tmp_path):
    assistant = make_assistant(tmp_path)

    capture_answer = assistant.handle_text("I'm currently debugging Azure auth")
    retrieval_answer = assistant.handle_text("What was I doing?")

    assert "Captured [CONTEXT]" in capture_answer
    assert "debugging Azure auth" in retrieval_answer


def test_router_distinguishes_capture_from_retrieval():
    router = QueryRouter()

    assert router.route("What did I say about email?").intent == "retrieval"
    assert router.route("I need to send that invoice tonight.").intent == "capture"
