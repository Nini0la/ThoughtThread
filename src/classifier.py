from __future__ import annotations

import re
from dataclasses import dataclass


MEMORY_TYPES = {"TASK", "CONTEXT", "REMINDER", "QUESTION", "NOTE"}


@dataclass(frozen=True)
class ClassifiedEntry:
    cleaned_text: str
    entry_type: str
    due_at: str | None
    tags: list[str]
    metadata_json: dict[str, str]


class Classifier:
    """Small deterministic classifier for the MVP text-first loop."""

    def classify(self, text: str) -> ClassifiedEntry:
        cleaned = clean_text(text)
        lowered = cleaned.lower()
        entry_type = _entry_type(lowered)
        due_at = _extract_due_hint(lowered)
        tags = _extract_tags(lowered)
        return ClassifiedEntry(
            cleaned_text=cleaned,
            entry_type=entry_type,
            due_at=due_at,
            tags=tags,
            metadata_json={"classifier": "rules-v1"},
        )


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _entry_type(lowered: str) -> str:
    if lowered.endswith("?"):
        return "QUESTION"
    if re.search(r"\b(currently|right now|working on|debugging|in the middle of)\b", lowered):
        return "CONTEXT"
    if re.search(r"\b(remind me|remember to|don't forget|need to check|check my|before|by )\b", lowered):
        if re.search(r"\b(send|reply|call|finish|submit|pay|book|schedule|review|write)\b", lowered):
            return "TASK"
        return "REMINDER"
    if re.search(r"\b(i need to|need to|todo|to do|should|must|have to|gotta)\b", lowered):
        return "TASK"
    if re.search(r"\b(invoice|due|tonight|tomorrow|today|before|by \d)", lowered):
        return "REMINDER"
    return "NOTE"


def _extract_due_hint(lowered: str) -> str | None:
    patterns = [
        r"\bbefore\s+([a-z0-9: ]+)$",
        r"\bby\s+([a-z0-9: ]+)$",
        r"\btonight\b",
        r"\btomorrow\b",
        r"\btoday\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, lowered)
        if match:
            return match.group(0)
    return None


def _extract_tags(lowered: str) -> list[str]:
    tags: list[str] = []
    for keyword in ("email", "invoice", "azure", "auth", "debugging", "reminder"):
        if keyword in lowered:
            tags.append(keyword)
    return tags

