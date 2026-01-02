import os, requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 從環境變數讀取金鑰
LINE_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not LINE_SECRET or not LINE_TOKEN:
    raise RuntimeError("❌ LINE env vars not set")

line_bot = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

@app.route("/", methods=["GET"])
def home():
    return "NTU Bot is running"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        # 當 LINE Verify 測試時可能觸發，回傳 400 是正常的
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    # 修正：使用 POST 方法呼叫 Cofacts API，避免中文亂碼與 URL 錯誤
    api_url = "https://cofacts-api.g0v.tw/graphql"
    
    # GraphQL 查詢結構
    query_json = {
        "query": """
        query($text: String) {
          ListArticles(filter: {text: $text}, first: 1) {
            nodes {
              text
            }
          }
        }
        """,
        "variables": {"text": msg}
    }

    try:
        # 加上 Header 確保 API 辨識正確
        headers = {"Content-Type": "application/json"}
        res = requests.post(api_url, json=query_json, headers=headers, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            articles = data.get("data", {}).get("ListArticles", {}).get("nodes", [])
            
            if articles:
                reply = "🔍 查核提醒：此訊息在 Cofacts 有紀錄"
            else:
                reply = "✅ 查無此訊息的查核紀錄"
        else:
            reply = "❌ 查核伺服器回應異常，請稍後再試"
            
    except Exception as e:
        print(f"Error: {e}")
        reply = "❌ 查核服務暫時無法使用"

    # 回覆訊息給使用者
    line_bot.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run()
