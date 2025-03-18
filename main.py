import requests
import os
import datetime
import random
from flask import Flask, request, jsonify
from utils import count_consecutive_days  # 祝日対応の連続日数計算

# グローバル変数で確率を管理
user_probabilities = {}

# 連続達成日数ごとの確率テーブル
streak_probabilities = {
    1:  {"1等": 2, "2等": 3, "3等": 5, "4等": 10, "5等": 80},
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
    data = {
        "user": user,
        "result": result,
        "streak": streak
    }
    requests.post(SHEET_WEBHOOK_URL, json=data)

# 抽選を実行
def draw_treasure(user_id, user_name, streak):
    global user_probabilities

    # 確率を取得またはデフォルトを使用
    if user_id not in user_probabilities:
        user_probabilities[user_id] = streak_probabilities.get(streak, streak_probabilities[5])

    probabilities = user_probabilities[user_id]

    # 抽選処理
    draw = random.uniform(0, 100)
    cumulative = 0
    result = "5等"
    
    for rank, prob in probabilities.items():
        cumulative += prob
        if draw <= cumulative:
            result = rank
            break

    # 当選画像とメッセージ
    images = {
        "1等": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/50en.png",
        "2等": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/100en.png",
        "3等": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/cake.png",
        "4等": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/aburasoba.jpg",
        "5等": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/supajyapo.png"
    }

    message = f"おめでとう！{user_name}は{result}が当たったよ🎉"

    # 個別通知
    send_reply(user_id, [
        {"type": "text", "text": message},
        {"type": "image", "originalContentUrl": images[result], "previewImageUrl": images[result]}
    ])

    # グループ通知
    group_message = f"{user_name} が {result} を当てました！🎊"
    send_message_to_group([
        {"type": "text", "text": group_message},
        {"type": "image", "originalContentUrl": images[result], "previewImageUrl": images[result]}
    ])

    # 結果をスプレッドシートに記録
    send_to_sheet(user_name, result, streak)

    # 1等なら確率リセット
    if result == "1等":
        user_probabilities[user_id] = streak_probabilities[5]


app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
GROUP_ID = "C0973bdef9d19444731d1ca0023f34ff3"

# ユーザーIDから名前を取得
def get_user_name(user_id):
    url = f"https://api.line.me/v2/bot/profile/{user_id}"
    headers = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        profile = response.json()
        return profile.get("displayName", "不明なユーザー")
    return "不明なユーザー"

# グループに通知
def send_message_to_group(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    }
    payload = {"to": GROUP_ID, "messages": message}
    requests.post(url, json=payload, headers=headers)

# 個別通知
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
    # イベント処理
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
