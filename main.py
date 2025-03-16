import requests
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")  # 環境変数からアクセストークンを取得

# ユーザーIDからユーザー名を取得する関数
def get_user_name(user_id):
    url = f"https://api.line.me/v2/bot/profile/{user_id}"
    headers = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        profile = response.json()
        return profile.get("displayName")
    else:
        print("Failed to get user profile:", response.status_code)
        return "不明なユーザー"

# グループにメッセージを送る関数（pushメッセージ）
def send_message_to_group(group_id, message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    }
    payload = {
        "to": group_id,
        "messages": [{"type": "text", "text": message}],
    }
    response = requests.post(url, json=payload, headers=headers)
    print("Response from LINE API (push):", response.json())

# 個別に返信する関数
def send_reply(reply_token, messages):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    }
    payload = {"replyToken": reply_token, "messages": messages}
    response = requests.post("https://api.line.me/v2/bot/message/reply", json=payload, headers=headers)
    print("Response from LINE API (reply):", response.json())

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Received data:", data)

    if "events" in data:
        for event in data["events"]:
            # 確実にメッセージイベントかつテキストがある場合に処理
            if event["type"] == "message" and "text" in event["message"]:
                source_type = event["source"]["type"]
                reply_token = event["replyToken"]
                user_message = event["message"]["text"]

                if user_message == "タスク完了":
                    # 「タスク完了」と送られたとき、確認画像とボタンを返信する
                    messages = [
                        {
                            "type": "image",
                            "originalContentUrl": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/sample.png",  # ここを正しい画像URLに変更
                            "previewImageUrl": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/sample.png",
                        },
                        {
                            "type": "template",
                            "altText": "タスクの確認",
                            "template": {
                                "type": "buttons",
                                "text": "やることはぜんぶおわりましたか？",
                                "actions": [
                                    {"type": "message", "label": "おわった！", "text": "はい"},
                                    {"type": "message", "label": "まだだった…", "text": "いいえ"},
                                ],
                            },
                        },
                    ]
                    send_reply(reply_token, messages)

                elif user_message == "おわった！":
                    if source_type == "group":
                        # グループ内の場合、ユーザーIDからユーザー名を取得してグループに通知する
                        user_id = event["source"].get("userId")
                        user_name = get_user_name(user_id) if user_id else "不明なユーザー"
                        group_message = f"{user_name}がタスクを完了しました！"
                        group_id = "C0973bdef9d19444731d1ca0023f34ff3"  # 実際のグループIDに置き換える
                        send_message_to_group(group_id, group_message)
                        print("Group notification sent; no reply in group chat.")
                        # ※グループ内では返信しない
                    else:
                        send_reply(reply_token, [{"type": "text", "text": "よくできました！"}])

                elif user_message == "まだだった…":
                    if source_type == "group":
                        print("No response for 'いいえ' in group chat.")
                        # グループ内の場合は何もしない
                    else:
                        send_reply(reply_token, [{"type": "text", "text": "今からしようね！"}])
                
                else:
                    # その他のメッセージは、個別の場合のみオウム返し
                    if source_type != "group":
                        send_reply(reply_token, [{"type": "text", "text": f"あなたのメッセージ: {user_message}"}])
                    else:
                        print("No response for other messages in group chat.")

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
