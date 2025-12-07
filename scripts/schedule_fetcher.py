import requests
from bs4 import BeautifulSoup
import datetime
import time
import random

class ScheduleFetcher:
    """
    ボートレース公式サイトから当日のレーススケジュールを取得するクラス
    """
    def __init__(self):
        # アクセス先ドメイン
        self.baseUrl = "https://www.boatrace.jp/owpc/pc/race"
        # アクセス拒否回避のためのヘッダー情報
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def fetchAllSchedules(self, targetDate=None):
        """
        指定された日付（デフォルトは当日）の全開催場のレーススケジュールを取得して返す
        
        Args:
            targetDate (str, optional): 取得対象日 (YYYYMMDD形式)。省略時は当日。

        Returns:
            list: レース情報の辞書リスト
                  [
                      {
                          'stadium': '桐生',
                          'jcd': '01',
                          'raceNo': 1,
                          'deadlineTime': '15:20',
                          'deadlineDatetime': datetime.datetimeオブジェクト
                      },
                      ...
                  ]
        """
        if targetDate is None:
            targetDate = datetime.datetime.now().strftime('%Y%m%d')
        
        print(f"スケジュール取得開始: {targetDate}")
        
        # 1. 開催中のレース場コード (jcd) を公式サイトのトップ一覧から特定する
        activeStadiums = self._getActiveStadiums(targetDate)
        if not activeStadiums:
            print("開催中のレース場が見つかりませんでした。")
            return []

        allSchedules = []

        # 2. 各レース場のスケジュールを取得
        for stadium in activeStadiums:
            jcd = stadium['jcd']
            stadiumName = stadium['name']
            print(f"取得中: {stadiumName} (JCD:{jcd})")
            
            schedules = self._getStadiumSchedule(jcd, targetDate)
            
            # レース場名などの情報を付与
            for race in schedules:
                race['stadium'] = stadiumName
            
            allSchedules.extend(schedules)
            
            # サーバー負荷軽減のため少し待機
            time.sleep(random.uniform(1.0, 2.0))

        print(f"全スケジュール取得完了: 合計 {len(allSchedules)} レース")
        return allSchedules

    def _fetchWithRetry(self, url, maxRetries=3):
        """
        リトライ機能付きのURL取得メソッド
        """
        for i in range(maxRetries):
            try:
                resp = requests.get(url, headers=self.headers, timeout=30)
                resp.raise_for_status()
                return resp
            except requests.exceptions.RequestException as e:
                print(f"接続エラー (試行 {i+1}/{maxRetries}): {e}")
                time.sleep(2)
        return None

    def _getActiveStadiums(self, dateStr):
        """
        開催中のレース場一覧を取得する内部メソッド
        """
        url = f"{self.baseUrl}/index?hd={dateStr}"
        resp = self._fetchWithRetry(url)
        if not resp:
            print("トップページの取得に失敗しました。")
            return []
            
        try:
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            stadiums = []
            uniqueJcds = set()

            for a in soup.find_all('a', href=True):
                href = a['href']
                if 'raceindex' in href and 'jcd=' in href:
                    try:
                        # URLパラメータからjcd抽出
                        qs = href.split('?')[1]
                        params = {p.split('=')[0]: p.split('=')[1] for p in qs.split('&')}
                        jcd = params.get('jcd')
                        
                        if jcd and jcd not in uniqueJcds:
                            # レース場名を画像altなどから取得を試みる
                            name = "不明"
                            img = a.find('img')
                            if img and img.get('alt'):
                                name = img.get('alt').replace('>', '') # 余計な記号除去
                            else:
                                text = a.get_text(strip=True)
                                if text:
                                    name = text
                            
                            stadiums.append({'jcd': jcd, 'name': name})
                            uniqueJcds.add(jcd)
                    except Exception as e:
                        print(f"レース場リンク解析エラー: {e}")
                        continue
            
            stadiums.sort(key=lambda x: x['jcd'])
            return stadiums
            
        except Exception as e:
            print(f"トップページ解析エラー: {e}")
            return []

    def _getStadiumSchedule(self, jcd, dateStr):
        """
        特定レース場のスケジュールを取得する内部メソッド
        """
        url = f"{self.baseUrl}/raceindex?jcd={jcd}&hd={dateStr}"
        scheduleList = []
        
        resp = self._fetchWithRetry(url)
        if not resp:
            return []
            
        try:
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            tables = soup.find_all('table')
            if not tables:
                return []
            
            # 最初のテーブルがスケジュール表
            table = tables[0]
            
            # tbodyに限定せず、テーブル内の全行を取得する
            # (複数のtbodyがある場合や、thead/tfootの構造に対応するため)
            rows = table.find_all('tr')
            
            # print(f"JCD{jcd}: Row count (all) = {len(rows)}")

            
            for i, row in enumerate(rows):
                cols = row.find_all('td')
                if len(cols) < 2:
                    continue
                
                try:
                    raceNoText = cols[0].get_text(strip=True).replace('R', '')
                    deadlineText = cols[1].get_text(strip=True)
                    
                    if raceNoText.isdigit() and ':' in deadlineText:
                        raceNo = int(raceNoText)
                        
                        dtStr = f"{dateStr} {deadlineText}"
                        deadlineDt = datetime.datetime.strptime(dtStr, "%Y%m%d %H:%M")
                        
                        scheduleList.append({
                            'jcd': jcd,
                            'raceNo': raceNo,
                            'deadlineTime': deadlineText,
                            'deadlineDatetime': deadlineDt
                        })
                except Exception as e:
                    continue


                    
        except Exception as e:
            print(f"スケジュールページ取得エラー (JCD:{jcd}): {e}")
            
        return scheduleList


if __name__ == "__main__":
    # テスト実行
    fetcher = ScheduleFetcher()
    schedules = fetcher.fetchAllSchedules()
    print("--- 取得結果サンプル ---")
    for s in schedules[:5]:
        print(s)
