import openai
import pickle
import os
from dotenv import load_dotenv
import google_custom_search
from flask import Flask, request, jsonify, session
from flask_cors import CORS

# 讀取 .env 檔案
load_dotenv()

if not os.getenv('SECRET_KEY'):
    secret_key = os.urandom(24)
    with open('.env', 'a') as f:
        # 將密鑰以 hex 格式寫入 .env 檔案
        f.write(f"SECRET_KEY={secret_key.hex()}\n") 

# 設定 OpenAI API 金鑰
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_ENGINE_ID = os.getenv('GOOGLE_ENGINE_ID')

# 設置 OpenAI API 金鑰
openai.api_key = OPENAI_API_KEY

# Google 搜尋工具設置
google = google_custom_search.CustomSearch(google_custom_search.RequestsAdapter(GOOGLE_API_KEY, GOOGLE_ENGINE_ID))

# 初始化 Flask
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

CORS(app)

# 讀取對話歷史紀錄
def load_history():
    if 'messages' not in session:
        # 如果 session 中沒有 messages，則檢查是否有檔案存儲對話紀錄
        if os.path.exists('chat_history.pkl'):
            with open('chat_history.pkl', 'rb') as f:
                session['messages'] = pickle.load(f)
        else:
            session['messages'] = [{"role": "system", "content": "請扮演一位智能助理，記住我說過的話"}]

# 儲存對話歷史紀錄
def save_history():
    with open('chat_history.pkl', 'wb') as f:
        pickle.dump(session['messages'], f)

def google_search(user_msg, num_results=5):
    content = "以下為已發生的事實：\n"
    for res in google.search(user_msg, num_results=num_results):
        content += f"標題：{res.title}\n摘要：{res.snippet}\n\n"
    content += "請依照上述事實回答以下問題。\n"
    return content

def chat_with_gpt(user_input, messages):
    messages.append({"role": "user", "content": user_input})
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            functions=[
                {
                    "name": "google_search",
                    "description": "使用 Google 搜尋查詢最新資訊",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "要搜尋的關鍵字"}
                        },
                        "required": ["query"]
                    }
                }
            ],
            function_call="auto"
        )
        reply = response.choices[0].message
        
        # 檢查是否需要 Google 搜尋
        if hasattr(reply, "function_call") and reply.function_call:
            # 確認 arguments 是否是字典，如果是字串，解析成字典
            if isinstance(reply.function_call.arguments, str):
                import json
                reply.function_call.arguments = json.loads(reply.function_call.arguments)
            
            search_query = reply.function_call.arguments["query"]
            search_results = google_search(search_query)
            messages.append({"role": "function", "name": "google_search", "content": search_results})
            # 重新呼叫 GPT
            return chat_with_gpt(user_input, messages) 
        
        return reply.content
    except openai.APIError as err:
        return f"發生錯誤：{err}"

@app.route("/", methods=['GET'])
def home():
        return "<h1>Chat Bot</h1>"

@app.route("/chat", methods=["POST"])
def chat():
    load_history()
    user_input = request.get_json(force=True).get("message", "").strip()
    if not user_input:
        return jsonify({"response": "請輸入內容"}), 400 

    # 聊天並更新歷史
    response = chat_with_gpt(user_input, session['messages'])
    session['messages'].append({"role": "assistant", "content": response})

    # 儲存更新後的對話歷史
    save_history()
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
