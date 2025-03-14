import requests
import os
from flask import Flask, request, jsonify

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
                            "originalContentUrl": "https://your-image-url.com/sample.png",  # 画像URLを正しいものに変更
                            "previewImageUrl": "https://your-image-url.com/sample.png",  # 画像URLを正しいものに変更
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

                # 「はい」や「いいえ」が押された場合の処理
                elif user_message == "はい":
                    group_id = "C0973bdef9d19444731d1ca0023f34ff3"  # ここにグループIDを設定
                    group_message = "○○がタスクを完了しました！"
                    send_message_to_group(group_id, group_message)
                    send_reply(reply_token, [{"type": "text", "text": "よくできました！"}])

                elif user_message == "いいえ":
                    send_reply(reply_token, [{"type": "text", "text": "今からしようね！"}])

                # ここではグループ内での反応には反応しない
                # グループ内での「はい」「いいえ」メッセージに反応しない
                elif event["source"]["type"] == "group" and event["type"] == "message":
                    # グループ内のメッセージには反応しない
                    pass

            # 他のメッセージの場合は、オウム返し
            else:
                reply_message = f"あなたのメッセージ: {user_message}"
                send_reply(reply_token, [{"type": "text", "text": reply_message}])

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
