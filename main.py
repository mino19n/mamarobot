import requests
import os
import datetime
from flask import Flask, request, jsonify
from utils import count_consecutive_days  # 祝日対応の連続日数計算

# スプレッドシートのWebhook URL（GASのURL）
SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzkHPpqJMJ14ZSDEiXWoN6iUZwDZ3ahagRLSMyCVyvMxv8PGzsV0Buqyul9zr2FLr0T/exec"

# スプレッドシートに記録する関数
def send_to_sheet(user, result, streak):
    data = {"user": user, "result": result, "streak": streak}  # 🔥 連続日数も記録
    requests.post(SHEET_WEBHOOK_URL, json=data)

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
        payload = {"to": GROUP_ID, "messages": message}
    requests.post(url, json=payload, headers=headers)

# 個別に返信する関数
def send_reply(reply_token, messages):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    }
    payload = {"replyToken": reply_token, "messages": messages}
    requests.post("https://api.line.me/v2/bot/message/reply", json=payload, headers=headers)

# スプレッドシートから達成日データを取得する関数
def get_user_task_dates(user):
    response = requests.get(SHEET_WEBHOOK_URL)
    if response.status_code == 200:
        data = response.json()
        user_records = data.get(user, [])
        return [datetime.datetime.strptime(d, "%Y-%m-%d").date() for d in user_records]
    return []

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
                            "originalContentUrl": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/task.png",
                            "previewImageUrl": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/task.png",
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
                
                if user_message == "おわった！":
                    send_reply(reply_token, [{"type": "text", "text": "よくできました！"}])
                    
                    if user_id:
                        user_name = get_user_name(user_id)
                        streak = count_consecutive_days(user_name)  # 🔥 連続日数を計算
                        group_message = f"{user_name}がタスクを完了しました！（{streak}日連続）"
                        send_message_to_group([{"type": "text", "text": group_message}])
                        # スプレッドシートに記録
                        send_to_sheet(user_name, user_message, streak)  # 🔥 修正
                
                elif user_message == "まだだった…":
                    send_reply(reply_token, [{"type": "text", "text": "今からしようね！"}])
                
                else:
                    send_reply(reply_token, [{"type": "text", "text": f"あなたのメッセージ: {user_message}"}])
    
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
