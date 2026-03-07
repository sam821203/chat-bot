"""
LangGraph agent: Ask mode (direct LLM, no tools) vs Agent mode (LLM + Google Search tool).
State: messages (LangChain message list), mode ("ask" | "agent").
Nodes: chatbot (calls LLM; ask = no tools, agent = with tools), tools (ToolNode).
Edges: START -> chatbot; chatbot -> conditional (Ask -> END, Agent + tool_calls -> tools else END); tools -> chatbot.
"""

import os
from typing import Annotated, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from tools import google_search

# ---------------------------------------------------------------------------
# State: messages (append-only), mode (read by chatbot node)
# ---------------------------------------------------------------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    mode: Literal["ask", "agent"]


# ---------------------------------------------------------------------------
# Chatbot node: if ask -> LLM without tools; if agent -> LLM with tools
# ---------------------------------------------------------------------------
def _chatbot_node(state: ChatState) -> dict:
    messages = state["messages"]
    mode = state["mode"]
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o"), temperature=0)
    if mode == "agent":
        llm = llm.bind_tools([google_search])
    response = llm.invoke(messages)
    return {"messages": [response]}


# ---------------------------------------------------------------------------
# Conditional edge: Ask -> END; Agent with tool_calls -> tools, else END
# ---------------------------------------------------------------------------
def _route_after_chat(state: ChatState) -> Literal["tools", "__end__"]:
    if state["mode"] == "ask":
        return "__end__"
    last = state["messages"][-1] if state["messages"] else None
    if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
        return "tools"
    return "__end__"


# ---------------------------------------------------------------------------
# Build graph: chatbot -> conditional -> tools (-> chatbot) or END
# ---------------------------------------------------------------------------
tool_node = ToolNode([google_search])
builder = StateGraph(ChatState)

builder.add_node("chatbot", _chatbot_node)
builder.add_node("tools", tool_node)

builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", _route_after_chat, {"tools": "tools", "__end__": END})
builder.add_edge("tools", "chatbot")

graph = builder.compile()
