import openai
import pickle
import os
from googlesearch import search
import json
from dotenv import load_dotenv

# 讀取 .env 檔案
load_dotenv()

# 設定 OpenAI API 金鑰
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_ENGINE_ID = os.getenv('GOOGLE_ENGINE_ID')

openai.api_key = OPENAI_API_KEY

# Google 搜尋工具設置
# google = google_custom_search.CustomSearch(google_custom_search.RequestsAdapter(GOOGLE_API_KEY, GOOGLE_ENGINE_ID))

# 記錄聊天歷史
HIST_FILE = "hist.dat"

def save_hist(hist):
    try:
        with open(HIST_FILE, 'wb') as f:
            pickle.dump(hist, f)
    except:
        print('無法寫入歷史檔')

def load_hist():
    try:
        with open(HIST_FILE, 'rb') as f:
            return pickle.load(f)
    except:
        print('無法開啟歷史檔')
        return []

def google_search(query, num_results=5):
  """
  使用 `googlesearch-python` 來搜尋 Google，並返回前 `num_results` 筆結果。

  :param query: 搜尋關鍵字
  :param num_results: 要獲取的搜尋結果數量
  :return: 格式化的搜尋結果字串
  """
  print(f"===== 啟動 Google 搜尋: {query} =====")
  results = "以下為已發生的事實：\n"

  try:
      for i, result in enumerate(search(query, num=num_results), start=1):
          results += f"{i}. {result}\n"

      results += "請依照上述事實回答以下問題。\n"
  except Exception as e:
      results = f"Google 搜尋時發生錯誤: {e}"

  return results

def chat_with_gpt(user_input, messages):
    messages.append({"role": "user", "content": user_input})
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-1106",
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
        
        if hasattr(reply, "function_call") and reply.function_call:
          # 打印 function_call 內容來確認結構
          # print(f"function_call: {reply.function_call}")
          
          # 確認 arguments 是否是字典，如果是字串，解析成字典
          if isinstance(reply.function_call.arguments, str):
              import json
              reply.function_call.arguments = json.loads(reply.function_call.arguments)
          
          # 現在可以安全地存取 query
          search_query = reply.function_call.arguments["query"]
          search_results = google_search(search_query)
          messages.append({"role": "function", "name": "google_search", "content": search_results})
          return chat_with_gpt(user_input, messages)  # 重新呼叫 GPT
        
        messages.append({"role": "assistant", "content": reply.content})
        return reply.content
    except openai.APIError as err:
        return f"發生錯誤：{err}"

# 初始化聊天歷史
messages = load_hist()
if not messages:
    messages.append({"role": "system", "content": "請扮演一位智能助理，記住我說過的話"})

# 交互式聊天
while True:
    user_input = input("使用者輸入：")
    if not user_input.strip():
        break
    response = chat_with_gpt(user_input, messages)
    print(f"ChatGPT API：{response}\n")

# 儲存歷史記錄
save_hist(messages)
