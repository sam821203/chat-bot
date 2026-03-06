import pickle
import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from graph import graph

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

# 讀取對話歷史紀錄
def load_history():
    if 'messages' not in session:
        if os.path.exists('chat_history.pkl'):
            with open('chat_history.pkl', 'rb') as f:
                session['messages'] = pickle.load(f)
        else:
            session['messages'] = [{"role": "system", "content": "請扮演一位智能助理，記住我說過的話"}]

# 儲存對話歷史紀錄
def save_history():
    with open('chat_history.pkl', 'wb') as f:
        pickle.dump(session['messages'], f)


def _session_messages_to_lc(messages):
    """Convert session message dicts (role/content) to LangChain message objects."""
    out = []
    for m in messages:
        role, content = m.get("role", "user"), m.get("content", "")
        if role == "system":
            content = content + "\n今天的日期是 " + datetime.now().strftime("%Y年%m月%d日") + "。"
            out.append(SystemMessage(content=content))
        elif role == "user":
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
    load_history()
    body = request.get_json(force=True) or {}
    user_input = (body.get("message") or "").strip()
    mode = body.get("mode", "ask")
    if mode not in ("ask", "agent"):
        mode = "ask"
    if not user_input:
        return jsonify({"response": "請輸入內容"}), 400

    # Append user message to session history
    session['messages'].append({"role": "user", "content": user_input})

    # Convert session messages to LangChain format and invoke graph
    lc_messages = _session_messages_to_lc(session['messages'])
    try:
        result_state = graph.invoke({"messages": lc_messages, "mode": mode})
    except Exception as err:
        session['messages'].pop()  # rollback user message
        return jsonify({"response": f"發生錯誤：{err}"}), 500

    response = _last_ai_content_from_state(result_state)
    session['messages'].append({"role": "assistant", "content": response})
    save_history()
    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
