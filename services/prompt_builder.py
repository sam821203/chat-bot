"""Builds system prompt for the chat agent from mode, date, and optional search result."""

from datetime import datetime

SYSTEM_PROMPT = """請扮演一位智能助理，記住我說過的話

若你有 Google 搜尋工具可用，且用戶問題涉及「最近／最新／目前／現在／今年／近期」等時間、或「戰爭／衝突／疫情／選舉」等進行中事件、或具體數字與日期（如股價、人數、何時發生）、或用戶明確要求查最新資料，你必須先使用 Google 搜尋取得即時資訊再回答，不可僅依賴既有知識直接回答。

If you have the Google Search tool available and the user's question involves time-related terms (e.g. recent, latest, current, now, this year), ongoing events (e.g. war, conflict, pandemic, election), specific numbers or dates (e.g. stock price, casualty count, when something happened), or the user explicitly asks to look up the latest information, you must call the Google Search tool first to get up-to-date information before answering; you must not answer from memory alone for such questions.

回覆請使用 Markdown 格式：適當使用標題（##、###）、條列（- 或 1.）、粗體、行內或區塊程式碼（` 或 ```），長文請分段以利閱讀。"""

AGENT_MUST_SEARCH_REMINDER = """你現在處於智慧助理模式且擁有 Google 搜尋工具。對於涉及「最近」「戰爭」「最新」「目前」等問題，你必須先呼叫 google_search 取得結果再回答，不可跳過搜尋直接回答。

You are in Agent mode with Google Search. For questions involving "recent", "war", "latest", "current", you must call google_search first and must not skip it."""

# 注入搜尋結果後給模型的指示：優先較新來源、註明時效
SEARCH_RESULT_INSTRUCTION = """請優先依據較新、較可靠的來源回答。若搜尋結果沒有明確日期或來源，請說明「根據搜尋到的報導」，並註明「若資訊有更新請以最新消息為準」，勿將單一舊報導陳述為確定事實。"""

# Ask 模式專用：無搜尋工具時，改為提示用戶切換 Agent mode
ASK_MODE_NO_SEARCH_INSTRUCTION = """你目前處於 Ask 模式，沒有 Google 搜尋工具，無法代為搜尋。
若用戶問題涉及「最近／最新／目前／即時」或明確要求查最新資料，禁止說「我將使用 Google 搜尋」「請稍等我去查」「幫你查」等語。
此類問題你必須直接、簡短回覆：若要查詢最新資料，請切換到 Agent mode（智慧助理模式）。"""


def build_system_prompt(
    mode: str,
    date: datetime,
    last_user_content: str = "",
    search_result: str | None = None,
    search_error: str | None = None,
) -> str:
    """Build full system prompt from mode, current date, and optional search result/error."""
    system_content = SYSTEM_PROMPT + "\n今天的日期是 " + date.strftime("%Y年%m月%d日") + "。"
    if mode == "ask":
        system_content += "\n\n" + ASK_MODE_NO_SEARCH_INSTRUCTION
    elif mode == "agent":
        system_content += "\n\n" + AGENT_MUST_SEARCH_REMINDER
        if search_result is not None:
            system_content += "\n\n以下是針對用戶問題的 Google 搜尋結果，請根據以下內容回答：\n\n" + search_result
            system_content += "\n\n" + SEARCH_RESULT_INSTRUCTION
        elif search_error is not None:
            system_content += "\n\n（搜尋時發生錯誤，請依既有知識回答：{})".format(search_error)
    return system_content


class SystemPromptBuilder:
    """Builds the system prompt for the chat agent."""

    def build(
        self,
        mode: str,
        date: datetime,
        last_user_content: str = "",
        search_result: str | None = None,
        search_error: str | None = None,
    ) -> str:
        return build_system_prompt(
            mode=mode,
            date=date,
            last_user_content=last_user_content,
            search_result=search_result,
            search_error=search_error,
        )
