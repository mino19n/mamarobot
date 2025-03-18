import requests
import os
import datetime
import random
from flask import Flask, request, jsonify, abort
from utils import count_consecutive_days  # 祝日対応の連続日数計算
from linebot.v3.messaging import MessagingApi
from linebot.v3.webhook import WebhookHandler, WebhookParser

line_bot_api = MessagingApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = Flask(__name__)

# LINE設定
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")  # 環境変数からアクセストークンを取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")  # 環境変数から取得

handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ✅ /callbackエンドポイントを追加
@app.route('/callback', methods=['POST'])
def callback():
    # LINEからの署名を取得
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        # イベント処理
        handler.handle(body, signature)
        print("イベントを処理しました！")
    except InvalidSignatureError:
        print("署名エラー")
        return 'Invalid signature', 400
    except Exception as e:
        print(f"エラー: {e}")
        return 'Error', 500

    # 成功時にLINEに200 OKを返す
    return 'OK', 200

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
SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxFpZk9UwpbR6QSXgvIshdx3zIuVZ7g3Z98UfBJrcMKqnQZWr4jfP9ccvsjaw0YlzA-/exec"

# スプレッドシートに記録する関数
def send_to_sheet(user, result, streak):
    data = {"user": user, "result": result, "streak": streak}  # 🔥 連続日数も記録
    requests.post(SHEET_WEBHOOK_URL, json=data)

# 抽選を実行
# 抽選関数内ではリセットしない
def draw_treasure(user_id, user_name, streak):
    global user_probabilities

    # 初回時に確率をセット
    if user_id not in user_probabilities:
        user_probabilities[user_id] = streak_probabilities.get(5)

    # 連続日数に応じた確率を取得
    probabilities = streak_probabilities.get(streak, user_probabilities[user_id])

    # 抽選処理
    draw = random.uniform(0, 100)
    cumulative = 0
    result = "5等"

    for rank, prob in probabilities.items():
        cumulative += prob
        if draw <= cumulative:
            result = rank
            break

    # 1等が出たら確率をリセット
    if result == "1等":
        user_probabilities[user_id] = streak_probabilities.get(5)

    # 通知処理
    images = {
        "1等": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/50en.png",
        "2等": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/100en.png",
        "3等": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/cake.png",
        "4等": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/aburasoba.jpg",
        "5等": "https://raw.githubusercontent.com/mino19n/mamarobot/main/images/supajyapo.png"
    }
    message = f"おめでとう！{user_name}は{result}が当たったよ🎉"

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

    # ✅ 結果をスプレッドシートに記録
    send_to_sheet(user_name, result, streak)

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
def get_user_task_dates(user_id, user_name=None):
    response = requests.get(SHEET_WEBHOOK_URL)
    if response.status_code == 200:
        data = response.json()
        if user_name:
            return data.get(user_id, []) or data.get(user_name, [])
        return data.get(user_id, [])
    return []

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        event_data = request.get_json()
        
        for event in event_data.get("events", []):
            event_type = event.get("type")
    
            if event_type == "message" and "text" in event["message"]:
                user_id = event["source"]["userId"]
                message_text = event["message"]["text"]
    
                print(f"User: {user_id}, Message: {message_text}")
    
                # スプレッドシートに書き込み
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.append_row([now, message_text, user_id])
    
        return jsonify({"status": "ok"})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)})

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
                    send_message_to_group(messages)
                
                if user_message == "おわった！":
                    send_reply(reply_token, [{"type": "text", "text": "よくできました！"}])
            
                    if user_id:
                        user_name = get_user_name(user_id)
                        streak = count_consecutive_days(user_name)  # 連続日数を取得

                        if streak == 0:  # 最初は1からスタート
                            streak = 1
                        else:
                            streak += 1
                    
                        # E列に連続日数を更新
                        sheet.update_cell(len(data), 5, streak)
                        
                        group_message = f"{user_name}がタスクを完了しました！（{streak}日連続）"
                        send_message_to_group([{"type": "text", "text": group_message}])
                
                        # 宝箱の閾値チェック
                        treasure_milestones = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65]
                        if streak in treasure_milestones:
                            send_message_to_group([
                                {"type": "text", "text": f"{user_name}は{streak}日連続達成！🎉"},
                                {"type": "image", "originalContentUrl": "https://example.com/treasure.gif", "previewImageUrl": "https://example.com/treasure.gif"},
                                {
                                    "type": "template",
                                    "altText": "宝箱を開ける！",
                                    "template": {
                                        "type": "buttons",
                                        "text": "おめでとう！宝箱を開けよう🎁",
                                        "actions": [
                                            {"type": "postback", "label": "宝箱を開ける！", "data": f"open_treasure,{user_id}"}
                                        ],
                                    },
                                },
                            ])
                            
                            # スプレッドシートに記録
                            result = request.json.get("result")  # 例: クライアントから受け取る場合
                            if result is None:
                                result = "default_value"  # 適切なデフォルト値を設定（例："未定義" など）
                                send_to_sheet(user_name, result, streak)
                
                elif user_message == "まだだった…":
                    send_reply(reply_token, [{"type": "text", "text": "今からしようね！"}])
                
                else:
                    send_reply(reply_token, [{"type": "text", "text": f"あなたのメッセージ: {user_message}"}])
                    
            elif event["type"] == "postback":
                data = event["postback"]["data"]
                if data.startswith("open_treasure"):
                    _, user_id = data.split(",")
                    user_name = get_user_name(user_id)
                    streak = count_consecutive_days(user_name)  # 連続日数を取得
                    draw_treasure(user_name, streak)  # 抽選処理
                
    return jsonify({"status": "ok"}), 200
    
# 宝箱を開けるハンドラ
@app.route("/treasure", methods=["POST"])
def open_treasure():
    data = request.json
    user_id = data["user_id"]
    user_name = data["user_name"]
    
    # 連続日数を取得
    streak = get_user_streak(user_id)  

    # 抽選処理
    result = draw_treasure(streak)

    # 抽選結果をスプレッドシートに記録
    record_treasure_result(user_id, user_name, streak, result)

    # 画像とメッセージを送信
    send_treasure_result(user_id, result)

    return jsonify({"status": "success", "result": result})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))  # 環境変数 PORT を取得（デフォルトは8080）
    app.run(host="0.0.0.0", port=port)
