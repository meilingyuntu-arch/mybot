import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 從環境變數讀取 LINE 密鑰
LINE_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

line_bot = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# 根路由，確認 BOT 運作中
@app.route("/", methods=["GET"])
def home():
    return "NTU Bot is running"

# 測試環境變數是否正確讀取
@app.route("/envtest", methods=["GET"])
def envtest():
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    secret = os.getenv("LINE_CHANNEL_SECRET")
    return f"LINE_CHANNEL_ACCESS_TOKEN: {token}<br>LINE_CHANNEL_SECRET: {secret}"

# LINE Webhook
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# 收到文字訊息事件時
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text

    # 串接 Cofacts 查核
    url = f"https://cofacts-api.g0v.tw/graphql?query={{ListArticles(filter:{{text:\"{msg}\"}},first:1){{nodes{{text}}}}}}"
    res = requests.get(url).json()

    reply = (
        "🔍 查核提醒：此訊息在 Cofacts 有紀錄"
        if res.get("data", {}).get("ListArticles", {}).get("nodes")
        else "✅ 查無此訊息的查核紀錄"
    )

    line_bot.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    # Render 會用 8080 port
    app.run(host='0.0.0.0', port=8080)
