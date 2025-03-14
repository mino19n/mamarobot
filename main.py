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
    # request.jsonの内容をログに出力
    data = request.json
    print("Received data:", data)  # ここでrequest.jsonの内容を確認

    # リクエストヘッダーとボディをログに出力
    print("Request Headers:", request.headers)
    print("Request Body:", request.get_data())  # これでPOSTリクエストのボディも確認できます

    # その他の処理（イベントをチェックなど）
    if "events" in data:
        for event in data["events"]:
            print("Event received:", event)  # イベント内容も確認

            if event["type"] == "message":
                print("Message received:", event["message"])  # メッセージ内容をログに出力

                if event["source"]["type"] == "group":
                    group_id = event["source"]["groupId"]
                    print("Group ID:", group_id)  # グループIDをログに出力

                # 受け取ったメッセージに応じた処理（例）
                reply_token = event["replyToken"]
                user_message = event["message"]["text"]

                if user_message == "タスク完了":
                    messages = [
                        {
                            "type": "text",
                            "text": "タスクが完了しました！"
                        }
                    ]
                    send_reply(reply_token, messages)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Renderの環境変数PORTを使う
    app.run(host="0.0.0.0", port=port, debug=True)  # デバッグモードを有効にする
