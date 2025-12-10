# ボートレース自動通知ツール (Boatrace Monitor)

GitHub Actionsを利用して、ボートレース場での「堅いレース（1号艇が強いレース）」を24時間監視し、Discordに通知するツールです。

## 🚀 システム概要

このシステムは、**PCをつけっぱなしにする必要はありません**。
Google Apps Script (GAS) が「正確な時計」としてトリガーを引き、クラウド上の GitHub Actions が処理を実行します。

1.  **Trigger**: GASが15分おきに起動。
2.  **Action**: GitHub Actions (`check_races_batch.py`) が実行される。
3.  **Check**:
    *   現在から **3分後〜18分後** に締切を迎えるレースを探す。
    *   対象レースの **単勝オッズ** を確認。
    *   **「1号艇が単勝一番人気（オッズ最低）」** の場合のみ通知対象とする。
    *   ※1号艇が不人気な（荒れそうな）レースは通知されません。
4.  **Notify**: Discordに「激熱レース」として通知が届く。

## 📂 フォルダ構成

```
.
├── .github/workflows/   # GitHub Actions設定ファイル (GASからのトリガーを受け取る)
├── scripts/             # Pythonスクリプト群
│   ├── check_races_batch.py  # [Main] メイン処理。時間判定と通知指示を行う。
│   ├── schedule_fetcher.py   # [Lib] 公式サイトから開催表やオッズを取得する。
│   ├── race_notifier.py      # [Lib] Discordへの通知送信を行う。
│   ├── monitor_races.py      # [Legacy] PCローカルで常時起動させておくための古いスクリプト。
│   └── inspect_schedule.py   # [Util] スケジュール確認用ツール。
├── requirements.txt     # Python依存ライブラリ一覧
├── PROJECT_ARCHITECTURE.md # 詳細な設計図と処理フロー図
└── README.md            # このファイル
```

## 🛠 メンテナンス

### 通知条件の変更
`scripts/check_races_batch.py` を編集します。
*   `MIN_OFFSET`: 検知開始時間（現在: 3分前）
*   `MAX_OFFSET`: 検知終了時間（現在: 18分前）

### オッズ条件の変更
`scripts/schedule_fetcher.py` の `check1stBoatPopularity` メソッドを編集します。

## ⚠️ 注意事項
*   `monitor_races.py` は古い方式（PC常時起動型）のスクリプトです。現在は使用していませんが、ローカルテスト用として残しています。
*   自動実行の間隔は GAS (Google Apps Script) 側で管理されています。GitHub側のみを変更しても間隔は変わりません。
