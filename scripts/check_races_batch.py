import datetime
from schedule_fetcher import ScheduleFetcher
from race_notifier import RaceNotifier
import os
import sys

# 時間オフセット設定
# Cronは5分おきに実行される。
# 通知タイミング: 3分前
# 
# 実行タイミングとカバー範囲:
# 00分実行: 03分後〜08分後のレースをチェック
# 05分実行: 08分後〜13分後のレースをチェック
# ...
# これにより、常に「3分前〜8分前」の範囲にあるレースを検知して通知する。
# 重複通知を防ぐため、このスクリプトはステートレス（状態を持たない）だが、
# 実行頻度とチェック範囲を調整してカバーする。
# ※ 正確に「3分前」ピンポイントではないが、許容範囲とする。

MIN_OFFSET = 3
MAX_OFFSET = 8

def check_and_notify():
    # 環境変数からWebhook URLを取得 (GitHub Secrets対応)
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL environment variable is not set.")
        sys.exit(1)

    # Notifierの初期化 (Configファイルではなく環境変数を使うように注入、あるいはNotifierを改造)
    # RaceNotifierはConfigを見に行く作りになっているため、一時的にConfig変数を上書きするか、
    # RaceNotifier自体をインスタンス化後にプロパティセットする。
    notifier = RaceNotifier()
    notifier.discordWebhookUrl = webhook_url

    print("Fetching today's schedule...")
    fetcher = ScheduleFetcher()
    schedules = fetcher.fetchAllSchedules()
    
    now = datetime.datetime.now()
    print(f"Current time: {now.strftime('%H:%M:%S')}")
    
    notify_count = 0
    
    for race in schedules:
        deadline_dt = race['deadlineDatetime']
        time_diff = deadline_dt - now
        minutes_left = time_diff.total_seconds() / 60
        
        # チェック範囲に入っているか
        if MIN_OFFSET <= minutes_left < MAX_OFFSET:
            print(f"Match: {race['stadium']} {race['raceNo']}R (Remaining: {minutes_left:.1f} min)")
            
            msg = f"{race['stadium']} {race['raceNo']}R\n締切: {race['deadlineTime']} (残り約{int(minutes_left)}分)"
            title = f"⏳ もうすぐ締切 ({int(minutes_left)}分前)"
            
            success = notifier.sendNotification(msg, title)
            if success:
                notify_count += 1
    
    print(f"Done. Sent {notify_count} notifications.")

if __name__ == "__main__":
    check_and_notify()
