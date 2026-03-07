"""Abstraction for executing search (e.g. Google) used by the chat service."""

from typing import Protocol


class SearchExecutor(Protocol):
    """Protocol for executing a search query."""

    def execute(self, query: str, num_results: int = 10) -> str:
        """Execute search and return result text."""
        ...


class DefaultSearchExecutor:
    """Default implementation using the google_search LangChain tool."""

    def __init__(self) -> None:
        from tools import google_search
        self._google_search = google_search

    def execute(self, query: str, num_results: int = 10) -> str:
        return self._google_search.invoke({"query": query, "num_results": num_results})
