import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")  # 環境変数からアクセストークンを取得

# グループにメッセージを送る関数
def send_message_to_group(group_id, message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    }
    payload = {
        "to": group_id,  # 送信先のグループID
        "messages": [
            {"type": "text", "text": message}
        ]
    }
    response = requests.post(url, json=payload, headers=headers)
    print("Response from LINE API:", response.json())

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
    print("Received data:", data)  # 受け取ったデータをログに出力

    if "events" in data:
        for event in data["events"]:
            if event["type"] == "message" and "text" in event["message"]:
                reply_token = event["replyToken"]
                user_message = event["message"]["text"]

                if user_message == "タスク完了":
                    messages = [
                        {
                            "type": "image",
                            "originalContentUrl": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/sample.png",
                            "previewImageUrl": "https://raw.githubusercontent.com/mino19n/mamarobot/blob/main/images/sample.png",
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

            elif event["type"] == "message" and "text" in event["message"]:
                reply_token = event["replyToken"]
                user_message = event["message"]["text"]

                if event["source"]["type"] == "group":
                    group_id = event["source"]["groupId"]
                    print("Group ID:", group_id)

                    if user_message == "はい":
                        # グループに通知する処理（グループIDを指定）
                        group_id = "YOUR_GROUP_ID"  # ここにグループIDを設定
                        group_message = "○○がタスクを完了しました！"
                        send_message_to_group(group_id, group_message)
                        send_reply(reply_token, [{"type": "text", "text": "よくできました！"}])

                    elif user_message == "いいえ":
                        send_reply(reply_token, [{"type": "text", "text": "今からしようね！"}])

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Renderの環境変数PORTを使う
    app.run(host="0.0.0.0", port=port)
