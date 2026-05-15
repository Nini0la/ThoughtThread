from __future__ import annotations

import re
from dataclasses import dataclass

from src.classifier import clean_text


@dataclass(frozen=True)
class RoutedInput:
    intent: str
    cleaned_text: str


class QueryRouter:
    def route(self, text: str) -> RoutedInput:
        cleaned = clean_text(text)
        if _is_retrieval_query(cleaned.lower()):
            return RoutedInput(intent="retrieval", cleaned_text=cleaned)
        return RoutedInput(intent="capture", cleaned_text=cleaned)


def _is_retrieval_query(lowered: str) -> bool:
    if not lowered:
        return False
    retrieval_patterns = [
        r"^what (was|am|should|did)\b",
        r"^what's (due|open|next)\b",
        r"^what was due\b",
        r"^what did i say about\b",
        r"^show recent\b",
        r"^list\b.*\b(tasks|reminders|notes|context)\b",
        r"^mark last task done\b",
        r"^complete last task\b",
        r"^done with last task\b",
    ]
    return any(re.search(pattern, lowered) for pattern in retrieval_patterns)

