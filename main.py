from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")  # 環境変数から取得

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Received:", data)  # ログ確認用

    # LINEのメッセージイベントがあるか確認
    if "events" in data:
        for event in data["events"]:
            if event["type"] == "message" and "text" in event["message"]:
                reply_token = event["replyToken"]
                user_message = event["message"]["text"]
                reply_message = f"あなたのメッセージ: {user_message}"  # 受け取ったメッセージをそのまま返す
                
                # LINEに返信
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
                }
                payload = {
                    "replyToken": reply_token,
                    "messages": [{"type": "text", "text": reply_message}],
                }
                requests.post("https://api.line.me/v2/bot/message/reply", json=payload, headers=headers)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
