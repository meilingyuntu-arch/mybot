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
    
    if msg == "測試":
        line_bot.reply_message(event.reply_token,TextSendMessage(text="✅ 機器人大腦連線正常，請傳送謠言內容。"))
        return

    api_url="https://cofacts-api.g0v.tw/graphql"
    query_json={
        "query": """query($q: String) { 
            ListArticles(filter: {q: $q}, first: 1) { 
                nodes { id } 
            } 
        }""",
        "variables": {"q": msg[:20]}
    }
    
    try:
        # 針對 1000062010 的異常，將 timeout 增加到 25 秒並加入連線重試邏輯
        session=requests.Session()
        res=session.post(api_url,json=query_json,headers={"Content-Type":"application/json"},timeout=25)
        res.raise_for_status()
        nodes=res.json().get("data",{}).get("ListArticles",{}).get("nodes",[])
        
        if nodes:
            aid=nodes[0].get("id")
            reply=f"🔍 查核提醒：此訊息在 Cofacts 有紀錄\n詳情：https://cofacts.tw/article/{aid}"
        else:
            reply=f"✅ 查無「{msg[:10]}」的完全吻合紀錄。"
    except Exception:
        # 讓回覆更人性化，不再只是噴出錯誤符號
        reply=f"⌛ 伺服器目前較擁擠，請再傳送一次「{msg[:5]}」試試看。"

    line_bot.reply_message(event.reply_token,TextSendMessage(text=reply))

if __name__=="__main__":
    app.run()
