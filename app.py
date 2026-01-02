import os, requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

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
        abort(400)
    except Exception as e:
        print("Webhook handler error:", e)
        abort(500)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text

    try:
        url = f"https://cofacts-api.g0v.tw/graphql?query={{ListArticles(filter:{{text:\"{msg}\"}},first:1){{nodes{{text}}}}}}"
        res = requests.get(url, timeout=5)
        data = res.json() if res.headers.get('Content-Type') == 'application/json' else {}
        nodes = data.get("data", {}).get("ListArticles", {}).get("nodes", [])
        if nodes:
            reply = "🔍 查核提醒：此訊息在 Cofacts 有紀錄"
        else:
            reply = "✅ 查無此訊息的查核紀錄"
    except Exception as e:
        print("Cofacts API error:", e)
        reply = "❌ 查核服務暫時無法使用"

    line_bot.reply_message(event.reply_token, TextSendMessage(text=reply))
