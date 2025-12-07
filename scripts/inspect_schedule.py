import requests
from bs4 import BeautifulSoup
import datetime

# 調査日時（本日）
date_str = datetime.datetime.now().strftime('%Y%m%d')
baseUrl = "https://www.boatrace.jp/owpc/pc/race"

# User-Agentヘッダー（アクセス拒否回避用）
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 1. 下関(19)のレース一覧ページを直接取得
urlIndex = f"{baseUrl}/raceindex?jcd=19&hd={date_str}"
print(f"下関ページ取得中: {urlIndex}")
resp = requests.get(urlIndex, headers=headers)
soup = BeautifulSoup(resp.content, 'html.parser')

# 直接詳細解析へ
targetUrl = urlIndex
# 以下は既存のロジックでsoupIdxなどを使っている箇所へ続くようにするが、
# ここでは script全体を書き換えた方がいいかもしれないが、
# 既存変数を上書きしてフローに乗せる。
respIdx = resp
soupIdx = soup


# 2. 解析実行
if True: # 強制実行
    print(f"詳細ページ解析: {targetUrl}")
    
    print("ページタイトル:", soupIdx.title.string)
    
    # テーブル要素を探す
    tables = soupIdx.find_all('table')
    if tables:
        print(f"テーブル数: {len(tables)}")
        # 最初のテーブルの構造を表示（締切時刻が含まれているか確認）
        # 特に、<th>や<td>の内容を確認して、締切時刻のカラムを探す
        rows = tables[0].find_all('tr')
        if rows:
            last_row = rows[-1]
            cols = last_row.find_all('td')
            if len(cols) > 1:
                print(f"12R締切時刻セル: '{cols[1].get_text(strip=True)}'")
            else:
                print("12Rのカラム数が不足しています")



        
        # もし複数のテーブルがあるなら、それらの概要も表示
        for i, tbl in enumerate(tables):
            rows = tbl.find_all('tr')
            print(f"テーブル {i}: 行数 {len(rows)}")
            if rows:
                print(f"  ヘッダー例: {rows[0].get_text(strip=True)[:50]}...")
    else:
        print("テーブルが見つかりませんでした。HTML構造がdivベースの可能性があります。")
        print("bodyの一部を表示します:")
        print(soupIdx.body.prettify()[:2000] if soupIdx.body else "bodyタグなし")

else:
    print("開催中のレース場が見つかりませんでした。")
