import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# === LINE 環境變數 ===
LINE_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# 防呆：避免 env 沒吃到卻默默回 400
if not LINE_SECRET or not LINE_TOKEN:
    raise RuntimeError("❌ LINE env vars not set")

line_bot = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)


# === 健康檢查（給 Render / 瀏覽器看）===
@app.route("/", methods=["GET"])
def home():
    return "NTU Bot is running"


# === LINE Webhook ===
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# === 收到文字訊息時 ===
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip()

    try:
        url = (
            "https://cofacts-api.g0v.tw/graphql"
            f"?query={{ListArticles(filter:{{text:\"{msg}\"}},first:1){{nodes{{text}}}}}}"
        )
        res = requests.get(url, timeout=5).json()

        if res.get("data", {}).get("ListArticles", {}).get("nodes"):
            reply = "🔍 查核提醒：此訊息在 Cofacts 有紀錄"
        else:
            reply = "✅ 查無此訊息的查核紀錄"

    except Exception:
        reply = "❌ 查核服務暫時無法使用"

    line_bot.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


# === 本地 / Render 啟動用 ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
