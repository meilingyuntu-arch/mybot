import os, requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 讀取環境變數
LINE_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

line_bot = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# 測試環境變數是否正確
@app.route("/envtest", methods=["GET"])
def envtest():
    if LINE_SECRET and LINE_TOKEN:
        return "環境變數已正確設定 ✅"
    else:
        return "環境變數未設定 ❌"

# callback route 保持 POST
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        print("Exception:", e)  # 例外也不會阻止回傳
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text

    # Cofacts 查核
    url = f"https://cofacts-api.g0v.tw/graphql?query={{ListArticles(filter:{{text:\"{msg}\"}},first:1){{nodes{{text}}}}}}"
    try:
        res = requests.get(url).json()
        reply = (
            "🔍 查核提醒：此訊息在 Cofacts 有紀錄"
            if res.get("data", {}).get("ListArticles", {}).get("nodes")
            else "✅ 查無此訊息的查核紀錄"
        )
    except Exception:
        reply = "❌ 查核服務暫時無法使用"

    line_bot.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

# 測試服務是否 running
@app.route("/", methods=["GET"])
def home():
    return "NTU Bot is running"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
