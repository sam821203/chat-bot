import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from graph import graph
from tools import google_search

# 讀取 .env 檔案
load_dotenv()

if not os.getenv('SECRET_KEY'):
    secret_key = os.urandom(24)
    with open('.env', 'a') as f:
        f.write(f"SECRET_KEY={secret_key.hex()}\n")

# 初始化 Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

CORS(app)

SYSTEM_PROMPT = """請扮演一位智能助理，記住我說過的話

若你有 Google 搜尋工具可用，且用戶問題涉及「最近／最新／目前／現在／今年／近期」等時間、或「戰爭／衝突／疫情／選舉」等進行中事件、或具體數字與日期（如股價、人數、何時發生）、或用戶明確要求查最新資料，你必須先使用 Google 搜尋取得即時資訊再回答，不可僅依賴既有知識直接回答。

If you have the Google Search tool available and the user's question involves time-related terms (e.g. recent, latest, current, now, this year), ongoing events (e.g. war, conflict, pandemic, election), specific numbers or dates (e.g. stock price, casualty count, when something happened), or the user explicitly asks to look up the latest information, you must call the Google Search tool first to get up-to-date information before answering; you must not answer from memory alone for such questions.

回覆請使用 Markdown 格式：適當使用標題（##、###）、條列（- 或 1.）、粗體、行內或區塊程式碼（` 或 ```），長文請分段以利閱讀。"""

AGENT_MUST_SEARCH_REMINDER = """你現在處於智慧助理模式且擁有 Google 搜尋工具。對於涉及「最近」「戰爭」「最新」「目前」等問題，你必須先呼叫 google_search 取得結果再回答，不可跳過搜尋直接回答。

You are in Agent mode with Google Search. For questions involving "recent", "war", "latest", "current", you must call google_search first and must not skip it."""

# 注入搜尋結果後給模型的指示：優先較新來源、註明時效
SEARCH_RESULT_INSTRUCTION = """請優先依據較新、較可靠的來源回答。若搜尋結果沒有明確日期或來源，請說明「根據搜尋到的報導」，並註明「若資訊有更新請以最新消息為準」，勿將單一舊報導陳述為確定事實。"""

# 觸發詞：含任一時即強制先執行 Google 搜尋再回答（僅 Agent 模式）
TRIGGER_KEYWORDS = {
    "最近", "最新", "目前", "現在", "今年", "近期", "即時",
    "戰爭", "衝突", "疫情", "選舉", "談判",
    "世足", "冠軍", "股價", "匯率", "查最新", "幫我查", "搜尋",
    "recent", "latest", "current", "now", "war", "election", "search",
}


def _should_force_search(content: str) -> bool:
    """若用戶訊息包含觸發詞則回傳 True（用於強制先搜再答）。"""
    if not content or not isinstance(content, str):
        return False
    text = content.strip()
    return any(kw in text for kw in TRIGGER_KEYWORDS)


def _client_messages_to_lc(messages):
    """Convert client message dicts (role/content) to LangChain message objects. Only user/assistant."""
    out = []
    for m in messages:
        role, content = m.get("role", "user"), m.get("content", "")
        if role == "user":
            out.append(HumanMessage(content=content))
        elif role == "assistant":
            out.append(AIMessage(content=content))
    return out


def _last_ai_content_from_state(state):
    """Extract response string from graph result: last AIMessage content."""
    messages = state.get("messages") or []
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            content = getattr(msg, "content", None) or ""
            if isinstance(content, str):
                return content
            # Multimodal content list
            return "".join(getattr(block, "text", str(block)) for block in content) if content else ""
    return ""


@app.route("/", methods=['GET'])
def home():
    return "<h1>Chat Bot</h1>"


@app.route("/chat", methods=["POST"])
def chat():
    body = request.get_json(force=True) or {}
    client_messages = body.get("messages")
    raw_mode = (body.get("mode") or "ask")
    mode_str = (raw_mode if isinstance(raw_mode, str) else str(raw_mode)).strip().lower()
    if mode_str == "agent" or mode_str.startswith("agent"):
        mode = "agent"
    elif mode_str == "ask" or mode_str.startswith("ask"):
        mode = "ask"
    else:
        mode = "ask"
    if not isinstance(client_messages, list) or len(client_messages) == 0:
        return jsonify({"response": "請提供 messages（非空陣列）"}), 400

    used_search = False
    system_content = SYSTEM_PROMPT + "\n今天的日期是 " + datetime.now().strftime("%Y年%m月%d日") + "。"
    if mode == "agent":
        system_content += "\n\n" + AGENT_MUST_SEARCH_REMINDER
        # 強制先搜再答：最後一則用戶訊息含觸發詞時，先執行搜尋並將結果寫入 system
        last_user_content = next(
            (m.get("content", "") for m in reversed(client_messages) if m.get("role") == "user"),
            "",
        )
        if _should_force_search(last_user_content):
            try:
                current_year = datetime.now().year
                query = f"{last_user_content} {current_year} 最新 現況"
                search_result = google_search.invoke({"query": query, "num_results": 10})
                system_content += "\n\n以下是針對用戶問題的 Google 搜尋結果，請根據以下內容回答：\n\n" + search_result
                system_content += "\n\n" + SEARCH_RESULT_INSTRUCTION
                used_search = True
            except Exception as search_err:
                system_content += "\n\n（搜尋時發生錯誤，請依既有知識回答：{})".format(str(search_err))
    lc_messages = [SystemMessage(content=system_content)] + _client_messages_to_lc(client_messages)
    try:
        result_state = graph.invoke({"messages": lc_messages, "mode": mode})
    except Exception as err:
        return jsonify({"response": f"發生錯誤：{err}"}), 500

    response = _last_ai_content_from_state(result_state)
    return jsonify({"response": response, "used_search": used_search})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
