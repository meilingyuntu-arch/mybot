import os
import requests
from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 從 Render 環境變數取得
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not LINE_TOKEN or not LINE_SECRET:
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
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text

    # Cofacts 正確 POST 呼叫
    graphql_query = {
        "query": """
        query($text: String!) {
          ListArticles(filter:{text:$text}, first:1) {
            nodes {
              text
            }
          }
        }
        """,
        "variables": {"text": user_msg}
    }

    try:
        res = requests.post("https://cofacts-api.g0v.tw/graphql", json=graphql_query, timeout=5).json()
        nodes = res.get("data", {}).get("ListArticles", {}).get("nodes")
        if nodes:
            reply = "🔍 查核提醒：此訊息在 Cofacts 有紀錄"
        else:
            reply = "✅ 查無此訊息的查核紀錄"
    except Exception as e:
        reply = "❌ 查核服務暫時無法使用"

    line_bot.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
