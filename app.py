import os, requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

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
    msg = event.message.text

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
