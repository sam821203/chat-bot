"""Orchestrates chat flow: validation, prompt building, search, graph invocation, response extraction."""

from datetime import datetime

from langchain_core.messages import SystemMessage

from services.dto import ChatRequest, ChatResponse, ValidationError
from services.graph_runner import GraphRunner
from services.message_converter import MessageConverter
from services.prompt_builder import SystemPromptBuilder
from services.search_executor import SearchExecutor
from services.search_trigger import SearchTriggerChecker


def _normalize_mode(raw_mode: str) -> str:
    """Normalize mode string to 'ask' or 'agent'."""
    mode_str = (raw_mode if isinstance(raw_mode, str) else str(raw_mode)).strip().lower()
    if mode_str == "agent" or mode_str.startswith("agent"):
        return "agent"
    return "ask"


def _last_user_content(messages: list[dict]) -> str:
    """Extract content of the last user message."""
    return next(
        (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
        "",
    )


class ChatService:
    """Service that executes one chat turn: validate, build prompt, optional search, run graph, return response."""

    def __init__(
        self,
        prompt_builder: SystemPromptBuilder,
        message_converter: MessageConverter,
        search_trigger: SearchTriggerChecker,
        graph_runner: GraphRunner,
        search_executor: SearchExecutor,
    ) -> None:
        self._prompt_builder = prompt_builder
        self._message_converter = message_converter
        self._search_trigger = search_trigger
        self._graph_runner = graph_runner
        self._search_executor = search_executor

    def execute(self, request: ChatRequest) -> ChatResponse:
        if not isinstance(request.messages, list) or len(request.messages) == 0:
            raise ValidationError("請提供 messages（非空陣列）")

        mode = _normalize_mode(request.mode)
        now = datetime.now()
        last_user_content = _last_user_content(request.messages)

        search_result: str | None = None
        search_error: str | None = None
        used_search = False

        if mode == "agent" and self._search_trigger.should_force_search(last_user_content):
            try:
                current_year = now.year
                query = f"{last_user_content} {current_year} 最新 現況"
                search_result = self._search_executor.execute(query, num_results=10)
                used_search = True
            except Exception as err:
                search_error = str(err)

        system_content = self._prompt_builder.build(
            mode=mode,
            date=now,
            last_user_content=last_user_content,
            search_result=search_result,
            search_error=search_error,
        )

        lc_messages = [SystemMessage(content=system_content)] + self._message_converter.client_to_lc(
            request.messages
        )

        result_state = self._graph_runner.invoke(
            messages=lc_messages,
            mode=mode,
            config={"recursion_limit": 25},
        )

        response_text = self._message_converter.extract_last_ai_content(result_state)
        return ChatResponse(response=response_text, used_search=used_search)
