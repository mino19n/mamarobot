const SHEET_ID = '1gIMniAC5igFdaOFMhs8AyEjZ7KPUrd41Ca2LBMqZ0o8';  // あなたのスプレッドシートIDに置き換え
const CHANNEL_ACCESS_TOKEN = "Qg6HS96zcEbuDufwoy/X9kKBKuYNgtvK85Q7FWuF67H+QpAirvRL2aXVDBIAjkDLapjyne+5SuM/g0O8kj0xKpcP8imALNKFMenRBnjFgND2gUPSf0Bkie0UYYfJ9S2fxjMhRLObVZ2oLlcZBvpONwdB04t89/1O/w1cDnyilFU=";
const GROUP_ID = 'C0973bdef9d19444731d1ca0023f34ff3';  // ← グループIDをここに記載

// ユーザー名を取得する関数
function getUserName(userId) {
  const url = `https://api.line.me/v2/bot/profile/${userId}`;

  const headers = {
    "Authorization": `Bearer ${CHANNEL_ACCESS_TOKEN}`
  };

  const options = {
    method: "get",
    headers: headers,
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);

  if (response.getResponseCode() === 200) {
    const data = JSON.parse(response.getContentText());
    return data.displayName;  // ユーザー名を返す
  } else {
    Logger.log(`ユーザー名取得失敗: ${response.getContentText()}`);
    return "不明なユーザー";  // エラー時はデフォルト表示
  }
}


function doPost(e) {
  // 📌 Webhookのデータをログで確認
  Logger.log(e ? e.postData.contents : 'データなし');
  try {
      const params = e ? JSON.parse(e.postData.contents) : null;

    if (params && params.events && params.events.length > 0) {
      const event = params.events[0];


      // ユーザーIDとメッセージ取得
      const replyToken = event.replyToken;
      const userId = event.source.userId;
      const messageText = event.message.text;

      // ユーザー名を取得
      const userName = getUserName(userId);  // 🔥 ユーザーIDから名前を取得

      // 日付と時間を取得
      const date = new Date();
      const time = date.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });

      // スプレッドシートに記録
      const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName("シート");

      if (messageText === "おわったよ！" || messageText === "まだだった…") {
        const row = [date.toLocaleDateString('ja-JP'), time, messageText, userName];  // ✅ ユーザー名で記録

        // LINEに返信
        const replyText = (messageText === "おわったよ！") ? "よくできました！" : "今からしようね！";
        sendReply(replyToken, replyText);

        // ✅ 「おわったよ！」ならスプレッドシートに記録してグループに通知
        if (messageText === "おわったよ！") {
          const groupMessage = `${userName}がやることを完了しました！🎉`;
          sendGroupMessage(GROUP_ID, groupMessage);

          sheet.appendRow(row);
        }


      }
    }
  } catch (error) {
    Logger.log("エラー: " + error);
  }
}

function sendReply(replyToken, messageText) {
 
  const url = 'https://api.line.me/v2/bot/message/reply';
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${CHANNEL_ACCESS_TOKEN}`
  };

  // 🔥 LINEは配列でメッセージを送信する必要がある
  const messages = [{ type: 'text', text: messageText }];

  const body = JSON.stringify({
    replyToken: replyToken,
    messages: messages
  });

  const options = {
    method: 'post',
    headers: headers,
    payload: body,
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);

  if (response.getResponseCode() !== 200) {
    Logger.log(`送信エラー: ${response.getContentText()}`);
  }
}

// 📌 グループに通知を送信
function sendGroupMessage(groupId, message) {
  const url = 'https://api.line.me/v2/bot/message/push';

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${CHANNEL_ACCESS_TOKEN}`
  };

  const body = JSON.stringify({
    to: groupId,
    messages: [{ type: 'text', text: message }]
  });

  const options = {
    method: 'post',
    headers: headers,
    payload: body,
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);
  if (response.getResponseCode() !== 200) {
    Logger.log(`グループ通知エラー: ${response.getContentText()}`);
  }
}
