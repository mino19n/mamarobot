from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")  # 環境変数から取得

# LINEメッセージ送信用の関数
def send_reply(reply_token, messages):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    }
    payload = {
        "replyToken": reply_token,
        "messages": messages,
    }
    requests.post("https://api.line.me/v2/bot/message/reply", json=payload, headers=headers)

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

                # 「タスク完了」と送られたら、確認画像とはい/いいえボタンを送る
                if user_message == "タスク完了":
                    messages = [
                        {
                            "type": "image",
                            "originalContentUrl": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/sample.png",
                            "previewImageUrl": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/sample.png",
                        },
                        {
                            "type": "template",
                            "altText": "タスクの確認",
                            "template": {
                                "type": "buttons",
                                "text": "これ終わった？",
                                "actions": [
                                    {"type": "message", "label": "はい", "text": "はい"},
                                    {"type": "message", "label": "いいえ", "text": "いいえ"},
                                ],
                            },
                        },
                    ]
                    send_reply(reply_token, messages)

                else:
                    # 通常のオウム返し
                    reply_message = f"あなたのメッセージ: {user_message}"
                    send_reply(reply_token, [{"type": "text", "text": reply_message}])

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
