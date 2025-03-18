import datetime
import holidays

jp_holidays = holidays.Japan()

def is_weekday(date):
    """土日・祝日を除いた平日かどうかを判定"""
    return date.weekday() < 5 and date not in jp_holidays

def count_consecutive_days(dates):
    if not dates:
        return 0

    print(f"Received dates: {dates}, type: {type(dates)}")  # 追加
    print(f"First element: {dates[0]}, type: {type(dates[0])}")  # 追加

    dates = sorted(dates, reverse=True)

    try:
        last_date = datetime.datetime.strptime(dates[0], "%Y-%m-%d")
    except ValueError as e:
        print(f"Error converting '{dates[0]}' to datetime: {e}")
        return 0  # エラー時は 0 を返す

    count = 1
    for i in range(1, len(dates)):
        next_date = last_date - datetime.timedelta(days=1)

        while not is_weekday(next_date):  
            next_date -= datetime.timedelta(days=1)

        try:
            date_obj = datetime.datetime.strptime(dates[i], "%Y-%m-%d")
        except ValueError as e:
            print(f"Error converting '{dates[i]}' to datetime: {e}")
            break

        if date_obj == next_date:
            count += 1
            last_date = next_date
        else:
            break

    print(f"連続日数: {count}日")
    return count

