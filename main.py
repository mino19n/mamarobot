import requests
import os
import datetime
import random
from flask import Flask, request, jsonify
from utils import count_consecutive_days  # 祝日対応の連続日数計算

# 連続達成日数ごとの確率テーブル
streak_probabilities = {
    5:  {"1等": 2, "2等": 3, "3等": 5, "4等": 10, "5等": 80},
    10: {"1等": 2, "2等": 3, "3等": 5, "4等": 15, "5等": 75},
    15: {"1等": 2, "2等": 3, "3等": 5, "4等": 17, "5等": 73},
    20: {"1等": 2, "2等": 3, "3等": 5, "4等": 20, "5等": 70},
    25: {"1等": 2, "2等": 3, "3等": 5, "4等": 22, "5等": 68},
    30: {"1等": 4, "2等": 5, "3等": 31, "4等": 30, "5等": 30},
    35: {"1等": 4, "2等": 5, "3等": 7, "4等": 34, "5等": 60},
    40: {"1等": 4, "2等": 5, "3等": 7, "4等": 34, "5等": 50},
    45: {"1等": 4, "2等": 5, "3等": 7, "4等": 28, "5等": 56},
    50: {"1等": 4, "2等": 5, "3等": 7, "4等": 34, "5等": 50},
    55: {"1等": 10, "2等": 14, "3等": 26, "4等": 30, "5等": 20},
    60: {"1等": 90, "2等": 5, "3等": 3, "4等": 1.5, "5等": 0.5},
    65: {"1等": 100, "2等": 0, "3等": 0, "4等": 0, "5等": 0}
}

# スプレッドシートのWebhook URL（GASのURL）
SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzkHPpqJMJ14ZSDEiXWoN6iUZwDZ3ahagRLSMyCVyvMxv8PGzsV0Buqyul9zr2FLr0T/exec"

# スプレッドシートに記録する関数
def send_to_sheet(user, result, streak):
    data = {"user": user, "result": result, "streak": streak}  # 🔥 連続日数も記録
    requests.post(SHEET_WEBHOOK_URL, json=data)

# 抽選を実行
def draw_treasure(user, streak):
    global user_probabilities

    # 連続日数に対応する確率を取得（デフォルトは 5 日の確率）
    probabilities = streak_probabilities.get(streak, streak_probabilities[5])

    # 抽選処理
    draw = random.uniform(0, 100)  # 0～100のランダムな値を取得
    cumulative = 0
    result = "5等"  # デフォルトは5等
    for rank, prob in probabilities.items():
        cumulative += prob
        if draw <= cumulative:
            result = rank
            break

    # 結果メッセージと画像を決定
    images = {
        "1等": "https://example.com/prize1.png",
        "2等": "https://example.com/prize2.png",
        "3等": "https://example.com/prize3.png",
        "4等": "https://example.com/prize4.png",
        "5等": "https://example.com/prize5.png"
    }
    message = f"おめでとう！{user}は{result}が当たったよ🎉"

    send_message_to_group([
        {"type": "text", "text": message},
        {"type": "image", "originalContentUrl": images[result], "previewImageUrl": images[result]}
    ])

    # 結果をスプレッドシートに記録
    send_to_sheet(user, result)

    # 1等なら確率をリセット（5日目の確率に戻す）
    if result == "1等":
        user_probabilities[user] = streak_probabilities[5]


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
                        streak = count_consecutive_days(user_name)  # 🔥 連続日数を計算
                        group_message = f"{user_name}がタスクを完了しました！（{streak}日連続）"
                        send_message_to_group(group_message)
                        # スプレッドシートに記録
                        send_to_sheet(user_name, user_message, streak)  # 🔥 修正
                
                elif user_message == "まだだった…":
                    send_reply(reply_token, [{"type": "text", "text": "今からしようね！"}])
                
                else:
                    send_reply(reply_token, [{"type": "text", "text": f"あなたのメッセージ: {user_message}"}])
    
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
