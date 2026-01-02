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

@app.route("/envtest")
def env_test():
    if LINE_SECRET and LINE_TOKEN:
        return "環境變數已正確設定 ✅"
    return "環境變數未設定 ❌"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        print("Error handling webhook:", e)
        abort(500)
    return "OK", 200

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

@app.route("/", methods=["GET"])
def home():
    return "NTU Bot is running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
