import os

from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

from services import ChatRequest, ChatResponse, ValidationError, create_chat_service

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


@app.route("/", methods=['GET'])
def home():
    return "<h1>Chat Bot</h1>"


@app.route("/chat", methods=["POST"])
def chat():
    body = request.get_json(force=True) or {}
    client_messages = body.get("messages")
    raw_mode = body.get("mode") or "ask"

    request_dto = ChatRequest(messages=client_messages or [], mode=raw_mode)
    service = create_chat_service()

    try:
        chat_response: ChatResponse = service.execute(request_dto)
        return jsonify({
            "response": chat_response.response,
            "used_search": chat_response.used_search,
        })
    except ValidationError as e:
        return jsonify({"response": e.message}), 400
    except Exception as err:
        return jsonify({"response": f"發生錯誤：{err}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=10000)
