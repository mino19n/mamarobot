import datetime
import holidays

jp_holidays = holidays.Japan()

def is_weekday(date):
    """土日・祝日を除いた平日かどうかを判定"""
    return date.weekday() < 5 and date not in jp_holidays

def count_consecutive_days(dates):
    """
    連続達成日数を計算（土日祝日はスキップ）
    :param dates: 達成日（昇順リスト: 'YYYY-MM-DD' の文字列形式）
    :return: 連続日数
    """
    if not dates:
        return 0

    # 最新の日付からチェック
    dates = sorted(dates, reverse=True)

    # 文字列 → datetime に変換
    last_date = datetime.datetime.strptime(dates[0], "%Y-%m-%d")
    count = 1

    for i in range(1, len(dates)):
        next_date = last_date - datetime.timedelta(days=1)

        # 土日・祝日はスキップ
        while not is_weekday(next_date):  
            next_date -= datetime.timedelta(days=1)

        # 連続しているか判定
        if datetime.datetime.strptime(dates[i], "%Y-%m-%d") == next_date:
            count += 1
            last_date = next_date  # 更新
        else:
            break

    return count
