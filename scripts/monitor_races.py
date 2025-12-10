import time
import datetime
from schedule_fetcher import ScheduleFetcher
from race_notifier import RaceNotifier

class RaceMonitor:
    """
    [LEGACY] PCローカル実行用クラス
    
    ※ 現在は GitHub Actions + GAS による自動実行 (check_races_batch.py) がメインです。
    このスクリプトは、PCを常時起動させて手元で動かす場合や、テスト目的でのみ使用してください。
    
    レーススケジュールを管理し、指定時間の前に通知を行うクラス
    """
    def __init__(self):
        self.fetcher = ScheduleFetcher()
        self.notifier = RaceNotifier()
        self.schedules = []
        self.notifiedRaces = set() # 通知済みレースのID (jcd_rno) を保持
        self.notificationOffsetMinutes = 3 # 何分前に通知するか

    def initialize(self):
        """
        起動時のデータ読み込み
        """
        # 今日のスケジュールを取得
        self.schedules = self.fetcher.fetchAllSchedules()
        print(f"監視対象: Total {len(self.schedules)} レース")

    def run(self):
        """
        メインループ。定期的に時間をチェックして通知を行う。
        """
        if not self.schedules:
            print("監視対象のレースがありません。終了します。")
            return

        print(f"監視を開始します... ({self.notificationOffsetMinutes}分前通知)")
        
        try:
            while True:
                self._checkAndNotify()
                
                # 次のチェックまで待機 (間隔は60秒)
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n監視を停止しました。")

    def _checkAndNotify(self):
        """
        現在時刻と各レースの締切時刻を比較し、条件を満たせば通知する
        """
        now = datetime.datetime.now()
        
        for race in self.schedules:
            # レース固有ID作成 (例: "02_01" -> 02場 1R)
            raceId = f"{race['jcd']}_{race['raceNo']}"
            
            if raceId in self.notifiedRaces:
                continue
            
            headlineDt = race['deadlineDatetime']
            
            # 締切までの残り時間（分）
            timeDiff = headlineDt - now
            minutesLeft = timeDiff.total_seconds() / 60
            
            # 判定ロジック:
            # 1. 残り時間が設定値(10)以下であること
            # 2. かつ、時間が過ぎ去っていないこと（締切後10分以内なら通知しても良いが、今回は締切前のみとする）
            #    -> minutesLeft > 0
            # 実際は「ちょうど10分前」を狙うが、ループ間隔のズレを考慮して
            # 「10分前〜0分前」の範囲に入った未通知レースを通知する運用にするのが確実。
            
            if 0 < minutesLeft <= self.notificationOffsetMinutes:
                # 通知メッセージ作成
                msg = f"{race['stadium']} {race['raceNo']}R\n締切: {race['deadlineTime']} (残り約{int(minutesLeft)}分)"
                title = f"⏳ 締切{self.notificationOffsetMinutes}分前通知"
                
                # 通知送信
                success = self.notifier.sendNotification(msg, title)
                if success:
                    print(f"通知完了: {raceId} - {msg.replace('\n', ' ')}")
                    self.notifiedRaces.add(raceId)

if __name__ == "__main__":
    monitor = RaceMonitor()
    monitor.initialize()
    monitor.run()
