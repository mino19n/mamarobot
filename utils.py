import datetime
import holidays
from datetime import datetime, timedelta
jp_holidays = holidays.Japan()

def is_weekday(date):
    """平日かどうかと祝日チェック"""
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
        last_date = datetime.strptime(last_date, "%Y-%m-%d")  # 例: "2025-03-17" の場合
        next_date = last_date - timedelta(days=1)

        while not is_weekday(next_date):  
            next_date -= datetime.timedelta(days=1)

        if dates[i] == next_date:
            count += 1
            last_date = next_date
        elif is_weekday(next_date):
            break

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
        last_date = datetime.strptime(last_date, "%Y-%m-%d")  # 例: "2025-03-17" の場合
        next_date = last_date - timedelta(days=1)

        while not is_weekday(next_date):  
            next_date -= datetime.timedelta(days=1)

        if dates[i] == next_date:
            count += 1
            last_date = next_date
        elif is_weekday(next_date):
            break

    return count
