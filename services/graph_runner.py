"""Abstraction for invoking the LangGraph chat graph."""

from typing import Any, Protocol

from langchain_core.messages import BaseMessage


class GraphRunner(Protocol):
    """Protocol for running the chat graph."""

    def invoke(
        self,
        messages: list[BaseMessage],
        mode: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Invoke the graph and return the final state."""
        ...


class DefaultGraphRunner:
    """Default implementation that uses the compiled LangGraph from graph module."""

    def __init__(self) -> None:
        from graph import graph as _graph
        self._graph = _graph

    def invoke(
        self,
        messages: list[BaseMessage],
        mode: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        config = config or {"recursion_limit": 25}
        return self._graph.invoke(
            {"messages": messages, "mode": mode},
            config=config,
        )
