import datetime
from schedule_fetcher import ScheduleFetcher
from race_notifier import RaceNotifier
import os
import sys

# 時間オフセット設定
# GASトリガーにより15分おきに実行される。
# 通知タイミング: 締切3分前〜18分前
# 
# 実行タイミングとカバー範囲:
# XX:00実行: 03分後〜18分後 (次の実行であるXX:15の3分後までカバー)
# XX:15実行: 18分後〜33分後
# ...
# これにより、常に「3分前〜18分前」の範囲にあるレースを検知して通知する。
# 重複通知を防ぐため、このスクリプトはステートレス（状態を持たない）だが、
# 実行頻度(15分)とチェック範囲(15分幅)を調整して漏れなくカバーする。

MIN_OFFSET = 3
MAX_OFFSET = 18

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
    
    # ディレクトリ作成 (念のため)
    os.makedirs('logs', exist_ok=True)
    log_file = 'logs/notification_history.csv'
    
    # CSVヘッダー書き込み (ファイルが存在しない場合のみ)
    if not os.path.exists(log_file):
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('ActionTime,RaceDate,Stadium,RaceNo,DeadlineTime,MinutesLeft\n')

    # スプレッドシート設定読み込み
    google_creds_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
    google_sheet_key = os.environ.get('GOOGLE_SHEET_KEY')
    sheet_client = None
    target_sheet = None

    if google_creds_json and google_sheet_key:
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            import json
            
            # JSON文字列から認証情報をロード
            creds_dict = json.loads(google_creds_json)
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            sheet_client = gspread.authorize(creds)
            
            # シートを開く
            workbook = sheet_client.open_by_key(google_sheet_key)
            # 最初のシートを取得、なければ作成等のエラーハンドリングはあえてシンプルにする
            target_sheet = workbook.sheet1
            print("Successfully connected to Google Spreadsheet.")
            
            # ヘッダーチェック (A1セルが空なら書き込む)
            if not target_sheet.cell(1, 1).value:
                target_sheet.append_row(['ActionTime', 'RaceDate', 'Stadium', 'RaceNo', 'DeadlineTime', 'MinutesLeft'])
                
        except Exception as e:
            print(f"Warning: Failed to connect to Google Sheets: {e}")

    # 通知対象レースを収集するリスト
    races_to_notify = []
    
    for race in schedules:
        deadline_dt = race['deadlineDatetime']
        time_diff = deadline_dt - now
        minutes_left = time_diff.total_seconds() / 60
        
        # チェック範囲に入っているか
        if MIN_OFFSET <= minutes_left < MAX_OFFSET:
            print(f"Match time: {race['stadium']} {race['raceNo']}R (Remaining: {minutes_left:.1f} min)")
            
            # オッズチェック (1号艇が1番人気か)
            jcd = race.get('jcd')
            raceNo = race.get('raceNo')
            
            # 日付またぎ対応 (念のため)
            race_date = deadline_dt.strftime('%Y%m%d')
            
            print(f"  Checking odds for {race['stadium']} {raceNo}R...")
            is_favorite = fetcher.check1stBoatPopularity(jcd, raceNo, race_date)
            
            if is_favorite is None:
                print(f"  -> Failed to fetch odds. Skipping.")
                continue
                
            if not is_favorite:
                print(f"  -> Skipped: 1st boat is NOT the favorite.")
                continue
            
            print(f"  -> Good! 1st boat IS the favorite. Adding to notification queue.")
            
            # 通知対象レースとして保存
            races_to_notify.append({
                'race': race,
                'minutes_left': minutes_left,
                'race_date': race_date
            })
    
    # 残り時間の短い順にソート
    races_to_notify.sort(key=lambda x: x['minutes_left'])
    
    # ソートされた順に通知を送信
    for race_info in races_to_notify:
        race = race_info['race']
        minutes_left = race_info['minutes_left']
        race_date = race_info['race_date']
        raceNo = race.get('raceNo')
        
        # 出走表URLを生成
        race_url = f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={raceNo}&jcd={int(race['jcd']):02d}&hd={race_date}"
        
        msg = f"{race['stadium']} {race['raceNo']}R\n締切: {race['deadlineTime']} (残り約{int(minutes_left)}分)\n✨ 1号艇1番人気鉄板レース予報 ✨\n{race_url}"
        title = f"🔥 激熱レース ({int(minutes_left)}分前)"
        
        success = notifier.sendNotification(msg, title)
        if success:
            notify_count += 1
            
            # ローカルCSVログ保存
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    # ActionTime, RaceDate, Stadium, RaceNo, DeadlineTime, MinutesLeft
                    action_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    log_line = f"{action_time},{race_date},{race['stadium']},{raceNo},{race['deadlineTime']},{minutes_left:.1f}\n"
                    f.write(log_line)
                print(f"  -> Log saved to {log_file}")
            except Exception as e:
                print(f"  -> Failed to save log: {e}")
            
            # スプレッドシートログ保存
            if target_sheet:
                try:
                    action_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    row_data = [action_time, race_date, race['stadium'], raceNo, race['deadlineTime'], f"{minutes_left:.1f}"]
                    target_sheet.append_row(row_data)
                    print(f"  -> Log saved to Google Sheet")
                except Exception as e:
                    print(f"  -> Failed to save to Google Sheet: {e}")
    
    print(f"Done. Sent {notify_count} notifications.")

if __name__ == "__main__":
    check_and_notify()
