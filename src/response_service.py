from __future__ import annotations

import re

from src.memory_store import MemoryEntry, MemoryStore


class ResponseService:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def answer(self, question: str) -> str:
        lowered = question.lower().strip()
        if lowered.startswith(("mark last task done", "complete last task", "done with last task")):
            return self._mark_last_task_done()
        if "what was i doing" in lowered or "what am i doing" in lowered:
            return self._recent_context()
        if "what should i be doing" in lowered:
            return self._open_work()
        if "what was due" in lowered or "what's due" in lowered:
            return self._due_items()
        if lowered.startswith("show recent tasks") or re.search(r"\blist\b.*\btasks\b", lowered):
            return self._recent_tasks()
        keyword = _keyword_query(lowered)
        if keyword:
            return self._keyword_mentions(keyword)
        return self._recent_summary()

    def _recent_context(self) -> str:
        entries = self.store.recent_entries(limit=5, entry_types=["CONTEXT", "NOTE"])
        if not entries:
            return "I do not have recent context yet."
        return "Recent context:\n" + _format_entries(entries)

    def _open_work(self) -> str:
        entries = self.store.recent_entries(limit=10, entry_types=["TASK", "REMINDER"], statuses=["open"])
        if not entries:
            return "I do not see any open tasks or reminders."
        return "Open tasks and reminders:\n" + _format_entries(entries)

    def _due_items(self) -> str:
        entries = [
            entry
            for entry in self.store.recent_entries(limit=20, entry_types=["TASK", "REMINDER"], statuses=["open"])
            if entry.due_at
        ]
        if not entries:
            return "I do not see anything due in recent memory."
        return "Recently due:\n" + _format_entries(entries)

    def _recent_tasks(self) -> str:
        entries = self.store.recent_entries(limit=10, entry_types=["TASK"], statuses=["open"])
        if not entries:
            return "I do not see any open tasks."
        return "Recent open tasks:\n" + _format_entries(entries)

    def _keyword_mentions(self, keyword: str) -> str:
        entries = self.store.search_entries(keyword, limit=10)
        if not entries:
            return f"I do not have recent mentions of {keyword}."
        return f"Recent mentions of {keyword}:\n" + _format_entries(entries)

    def _recent_summary(self) -> str:
        entries = self.store.recent_entries(limit=8)
        if not entries:
            return "I do not have anything in memory yet."
        return "Recent memory:\n" + _format_entries(entries)

    def _mark_last_task_done(self) -> str:
        entry = self.store.mark_last_task_done()
        if entry is None:
            return "I do not see an open task to mark done."
        return f"Marked done: {entry.cleaned_text}"


def _keyword_query(lowered: str) -> str | None:
    match = re.search(r"what did i say about (.+?)[?.]?$", lowered)
    if match:
        return match.group(1).strip()
    match = re.search(r"mentions? of (.+?)[?.]?$", lowered)
    if match:
        return match.group(1).strip()
    return None


def _format_entries(entries: list[MemoryEntry]) -> str:
    lines = []
    for entry in entries:
        due = f" due {entry.due_at}" if entry.due_at else ""
        status = f", {entry.status}" if entry.status != "open" else ""
        lines.append(f"- [{entry.entry_type}{status}] {entry.cleaned_text}{due}")
    return "\n".join(lines)

