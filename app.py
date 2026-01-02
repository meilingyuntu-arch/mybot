import os, requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app=Flask(__name__)

LINE_SECRET=os.getenv("LINE_CHANNEL_SECRET")
LINE_TOKEN=os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

line_bot=LineBotApi(LINE_TOKEN)
handler=WebhookHandler(LINE_SECRET)

@app.route("/",methods=["GET"])
def home():
    return "NTU Bot is running"

@app.route("/callback",methods=["POST"])
def callback():
    signature=request.headers.get("X-Line-Signature")
    body=request.get_data(as_text=True)
    try:
        handler.handle(body,signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent,message=TextMessage)
def handle_message(event):
    msg=event.message.text.strip()
    # 策略：只取前 50 個字搜尋，增加命中率
    search_text=msg[:50]
    
    api_url="https://cofacts-api.g0v.tw/graphql"
    # 使用 q 模糊搜尋，這是命中率最高的方式
    query_json={
        "query": """query($q: String) { 
            ListArticles(filter: {q: $q}, first: 1) { 
                nodes { id } 
            } 
        }""",
        "variables": {"q": search_text}
    }
    
    try:
        res=requests.post(api_url,json=query_json,headers={"Content-Type": "application/json"},timeout=10)
        data=res.json()
        nodes=data.get("data",{}).get("ListArticles",{}).get("nodes",[])
        
        if nodes:
            article_id=nodes[0].get("id")
            reply=f"🔍 查核提醒：此訊息在 Cofacts 有紀錄\n詳情：https://cofacts.tw/article/{article_id}"
        else:
            reply="✅ 查無此訊息的查核紀錄"
    except:
        reply="✅ 查無此訊息的查核紀錄"

    line_bot.reply_message(event.reply_token,TextSendMessage(text=reply))

if __name__=="__main__":
    app.run()
