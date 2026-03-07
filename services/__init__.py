"""Service layer for chat business logic."""

from services.chat_service import ChatService
from services.dto import ChatRequest, ChatResponse, ValidationError
from services.graph_runner import DefaultGraphRunner
from services.message_converter import MessageConverter
from services.prompt_builder import SystemPromptBuilder
from services.search_executor import DefaultSearchExecutor
from services.search_trigger import SearchTriggerChecker


def create_chat_service() -> ChatService:
    """Create a ChatService with default implementations (for app and production)."""
    return ChatService(
        prompt_builder=SystemPromptBuilder(),
        message_converter=MessageConverter(),
        search_trigger=SearchTriggerChecker(),
        graph_runner=DefaultGraphRunner(),
        search_executor=DefaultSearchExecutor(),
    )


__all__ = [
    "ChatService",
    "ChatRequest",
    "ChatResponse",
    "ValidationError",
    "create_chat_service",
]
