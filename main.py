import requests
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")  # 環境変数からアクセストークンを取得

# ユーザーIDからユーザー名を取得する関数（必要なら）
def get_user_name(user_id):
    url = f"https://api.line.me/v2/bot/profile/{user_id}"
    headers = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        profile = response.json()
        return profile.get("displayName")
    else:
        print("Failed to get user profile:", response.status_code)
        return None

# グループにメッセージを送る関数
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
    payload = {
        "replyToken": reply_token,
        "messages": messages,
    }
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
            # まずはメッセージイベントか確認
            if event["type"] == "message" and "text" in event["message"]:
                reply_token = event["replyToken"]
                user_message = event["message"]["text"]

                # グループか個別か判別
                source_type = event["source"]["type"]

                if user_message == "タスク完了":
                    # 「タスク完了」と送られたときは、確認画像とボタンを返信する
                    messages = [
                        {
                            "type": "image",
                            "originalContentUrl": "images/sample.png",  # 画像URLを正しいものに変更
                            "previewImageUrl": "images/sample.png",
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

                elif user_message == "はい":
                    # 「はい」が押された場合、ユーザー名を使ってグループに通知する
                    # グループ外であれば個別返信もするが、グループ内の場合は返信はしない
                    if source_type == "group":
                        # 例：個人のユーザー名を取得したい場合
                        user_id = event["source"].get("userId")
                        user_name = get_user_name(user_id) if user_id else "不明なユーザー"
                        group_message = f"{user_name}がタスクを完了しました！"
                        # ここでグループに通知する。グループIDは、事前に取得済みまたは設定済みのものを使用する
                        group_id = "YOUR_GROUP_ID"  # 実際のグループIDに置き換える
                        send_message_to_group(group_id, group_message)
                        # グループ内では返信はしない（または、必要ならログだけ出す）
                        print("Group notification sent; no reply in group chat.")
                    else:
                        # 個別チャットの場合は返信する
                        send_reply(reply_token, [{"type": "text", "text": "よくできました！"}])

                elif user_message == "いいえ":
                    # 「いいえ」の場合も同様に、個別チャットなら返信し、グループ内なら何もしない
                    if source_type == "group":
                        print("No response for 'いいえ' in group chat.")
                    else:
                        send_reply(reply_token, [{"type": "text", "text": "今からしようね！"}])

                else:
                    # その他のメッセージはオウム返し
                    if source_type != "group":  # 個別チャットの場合のみ返信
                        reply_message = f"あなたのメッセージ: {user_message}"
                        send_reply(reply_token, [{"type": "text", "text": reply_message}])
                    else:
                        print("No response for other messages in group chat.")

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
