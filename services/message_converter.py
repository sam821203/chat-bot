"""Convert between client message format and LangChain messages; extract AI content from state."""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def client_to_lc(messages: list[dict]) -> list[BaseMessage]:
    """Convert client message dicts (role/content) to LangChain message objects. Only user/assistant."""
    out: list[BaseMessage] = []
    for m in messages:
        role, content = m.get("role", "user"), m.get("content", "")
        if role == "user":
            out.append(HumanMessage(content=content))
        elif role == "assistant":
            out.append(AIMessage(content=content))
    return out


def extract_last_ai_content(state: dict) -> str:
    """Extract response string from graph result: last AIMessage content."""
    messages = state.get("messages") or []
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            content = getattr(msg, "content", None) or ""
            if isinstance(content, str):
                return content
            # Multimodal content list
            return (
                "".join(getattr(block, "text", str(block)) for block in content)
                if content
                else ""
            )
    return ""


class MessageConverter:
    """Converts client messages to LangChain format and extracts AI content from graph state."""

    @staticmethod
    def client_to_lc(messages: list[dict]) -> list[BaseMessage]:
        return client_to_lc(messages)

    @staticmethod
    def extract_last_ai_content(state: dict) -> str:
        return extract_last_ai_content(state)
