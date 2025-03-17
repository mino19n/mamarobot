import datetime
import holidays

jp_holidays = holidays.Japan()

def is_weekday(date):
    """土日・祝日を除いた平日かどうかを判定"""
    return date.weekday() < 5 and date not in jp_holidays

def count_consecutive_days(dates):
    """
    連続達成日数を計算（土日祝日はスキップ）
    :param dates: 達成日（昇順リスト）
    :return: 連続日数
    """
    if not dates:
        return 0

    dates = sorted(dates, reverse=True)  # 最新の日付からチェック
    count = 1
    last_date = dates[0]  # 直近の達成日

    for i in range(1, len(dates)):
        next_date = last_date - datetime.timedelta(days=1)

        while not is_weekday(next_date):  
            next_date -= datetime.timedelta(days=1)

        if dates[i] == next_date:
            count += 1
            last_date = next_date
        elif is_weekday(next_date):
            break

    return count
