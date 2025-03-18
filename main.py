import os
import requests
from flask import Flask, request, jsonify, abort
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.v3.webhook import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError

# 環境変数読み込み
load_dotenv()

# LINE設定
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# LINE API設定
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

app = Flask(__name__)

@app.route('/callback', methods=['POST'])
def callback():
    print("Webhookを受信しました！")

    # 署名を取得
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        print("署名がありません")
        abort(400)

    # リクエストボディを取得
    body = request.get_data(as_text=True)
    print("受信データ:", body)

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        print("署名エラー")
        abort(400)

    except Exception as e:
        print(f"エラー詳細: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

    for event in events:
        if event.type == "message":
            user_id = event.source.user_id
            message = event.message.text
            print(f"User: {user_id}, Message: {message}")
            
            line_bot_api.reply_message(
                event.reply_token,
                [{"type": "text", "text": f"あなたのメッセージ: {message}"}]
            )

    return 'OK', 200

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))  # 環境変数 PORT を取得（デフォルトは8080）
    app.run(host="0.0.0.0", port=port)
