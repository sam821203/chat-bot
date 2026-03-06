"""LangChain tools for the chatbot agent. Google Search uses google-custom-search."""

import os
import google_custom_search
from langchain_core.tools import tool

# Lazy-init search client so env is loaded when tool runs
_search_client = None


def _get_search_client():
    global _search_client
    if _search_client is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        engine_id = os.getenv("GOOGLE_ENGINE_ID")
        if not api_key or not engine_id:
            raise ValueError("GOOGLE_API_KEY and GOOGLE_ENGINE_ID must be set")
        _search_client = google_custom_search.CustomSearch(
            google_custom_search.RequestsAdapter(api_key, engine_id)
        )
    return _search_client


@tool
def google_search(query: str, num_results: int = 5) -> str:
    """使用 Google 搜尋查詢最新資訊。當需要即時或事實性資訊時使用此工具。
    query: 要搜尋的關鍵字或問題。
    """
    client = _get_search_client()
    content = "以下為已發生的事實：\n"
    for res in client.search(query, num_results=num_results):
        content += f"標題：{res.title}\n摘要：{res.snippet}\n\n"
    content += "請依照上述事實回答以下問題。\n"
    return content
