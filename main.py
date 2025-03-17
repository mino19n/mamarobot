import requests
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")  # 環境変数からアクセストークンを取得
GROUP_ID = "C0973bdef9d19444731d1ca0023f34ff3"  # 実際のグループIDに置き換える

# ユーザーIDからユーザー名を取得する関数
def get_user_name(user_id):
    url = f"https://api.line.me/v2/bot/profile/{user_id}"
    headers = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        profile = response.json()
        return profile.get("displayName", "不明なユーザー")
    return "不明なユーザー"

# グループにメッセージを送る関数（pushメッセージ）
def send_message_to_group(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    }
    payload = {"to": GROUP_ID, "messages": [{"type": "text", "text": message}]}
    requests.post(url, json=payload, headers=headers)

# 個別に返信する関数
def send_reply(reply_token, messages):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    }
    payload = {"replyToken": reply_token, "messages": messages}
    requests.post("https://api.line.me/v2/bot/message/reply", json=payload, headers=headers)

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Received data:", data)

    if "events" in data:
        for event in data["events"]:
            if event["type"] == "message" and "text" in event["message"]:
                source_type = event["source"]["type"]
                reply_token = event["replyToken"]
                user_message = event["message"]["text"]
                user_id = event["source"].get("userId")
                
                if source_type == "group":
                    print("Message from group; no response.")
                    continue  # グループ内のメッセージには一切反応しない
                
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
                                "text": "やることはぜんぶおわりましたか？",
                                "actions": [
                                    {"type": "message", "label": "おわった！", "text": "おわった！"},
                                    {"type": "message", "label": "まだだった…", "text": "まだだった…"},
                                ],
                            },
                        },
                    ]
                    send_reply(reply_token, messages)
                
                elif user_message == "おわった！":
                    send_reply(reply_token, [{"type": "text", "text": "よくできました！"}])
                    if user_id:
                        user_name = get_user_name(user_id)
                        group_message = f"{user_name}がタスクを完了しました！"
                        send_message_to_group(group_message)
                
                elif user_message == "まだだった…":
                    send_reply(reply_token, [{"type": "text", "text": "今からしようね！"}])
                
                else:
                    send_reply(reply_token, [{"type": "text", "text": f"あなたのメッセージ: {user_message}"}])
    
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
