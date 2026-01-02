import os, requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app=Flask(__name__)

LINE_SECRET=os.getenv("LINE_CHANNEL_SECRET")
LINE_TOKEN=os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot=LineBotApi(LINE_TOKEN)
handler=WebhookHandler(LINE_SECRET)

@app.route("/callback",methods=["POST"])
def callback():
    signature=request.headers.get("X-Line-Signature")
    body=request.get_data(as_text=True)
    try:
        handler.handle(body,signature)
    except:
        abort(400)
    return "OK"

@handler.add(MessageEvent,message=TextMessage)
def handle_message(event):
    msg=event.message.text.strip()
    
    # 預設測試掛鉤：如果傳「測試」，保證回傳內容
    if msg == "測試":
        line_bot.reply_message(event.reply_token,TextSendMessage(text="✅ 機器人大腦連線正常，請傳送謠言內容。"))
        return

    api_url="https://cofacts-api.g0v.tw/graphql"
    # 策略：改用最寬鬆的搜尋條件，並增加回傳欄位
    query_json={
        "query": """query($q: String) { 
            ListArticles(filter: {q: $q}, first: 1) { 
                nodes { id text } 
            } 
        }""",
        "variables": {"q": msg[:20]}
    }
    
    try:
        res=requests.post(api_url,json=query_json,headers={"Content-Type": "application/json"},timeout=10)
        nodes=res.json().get("data",{}).get("ListArticles",{}).get("nodes",[])
        
        if nodes:
            aid=nodes[0].get("id")
            reply=f"🔍 查核提醒：這則訊息在 Cofacts 有紀錄\n詳情：https://cofacts.tw/article/{aid}"
        else:
            # 沒查到時的引導，讓 Bot 不再像死掉一樣
            reply=f"✅ 查無「{msg[:10]}...」的完全吻合紀錄。\n💡 建議：縮短文字或至 cofacts.tw 手動查詢。"
    except:
        reply="❌ 查核服務暫時連線異常"

    line_bot.reply_message(event.reply_token,TextSendMessage(text=reply))

if __name__=="__main__":
    app.run()
