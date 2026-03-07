"""Data transfer objects and exceptions for the chat service."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChatRequest:
    """Input for a single chat turn."""

    messages: list[dict[str, Any]]
    mode: str  # normalized to "ask" or "agent"


@dataclass(frozen=True)
class ChatResponse:
    """Output of a single chat turn."""

    response: str
    used_search: bool


class ValidationError(Exception):
    """Raised when request validation fails (e.g. missing or invalid messages)."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
