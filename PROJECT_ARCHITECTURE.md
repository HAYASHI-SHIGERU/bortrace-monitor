# プロジェクト構成とワークフロー

このドキュメントでは、競艇通知ツールのシステム全体像と内部ロジックを解説します。

## 1. システム全体像 (Architecture)

Google Apps Script (GAS) が「正確な時計」として機能し、そこからのリクエストをトリガーに GitHub Actions が動き出します。

```mermaid
graph TD
    subgraph "Trigger System"
        GAS[Google Apps Script] -- "5~15分おきに実行" --> GH_API[GitHub API]
    end

    subgraph "Execution Environment (GitHub Actions)"
        GH_API -- "dispatch event" --> GH_ACT[Workflow: boatrace_monitor.yml]
        GH_ACT --> PY[Python Environment]
    end

    subgraph "Application Logic"
        PY --> MAIN[check_races_batch.py]
        MAIN --> FETCH[schedule_fetcher.py]
        MAIN --> NOTIFY[race_notifier.py]
    end

    subgraph "External Services"
        FETCH -- "スクレイピング" --> WEB[Boatrace Office Site]
        NOTIFY -- "Webhook" --> DISCORD[Discord]
    end
```

## 2. Pythonスクリプト詳細フロー

メインスクリプト `check_races_batch.py` を中心とした処理の流れです。

```mermaid
sequenceDiagram
    participant Main as check_races_batch.py
    participant Fetcher as schedule_fetcher.py
    participant Web as 公式サイト
    participant Notifier as race_notifier.py
    participant Discord as Discord

    Note over Main: 起動 (GitHub Actions)

    Main->>Fetcher: fetchAllSchedules()<br/>当日の全レース取得
    Fetcher->>Web: レース場一覧取得
    Fetcher->>Web: 各場タイムテーブル取得
    Web-->>Fetcher: HTMLデータ
    Fetcher-->>Main: レース情報リスト

    loop 各レースについてチェック
        Main->>Main: 締切までの時間を計算
        
        alt 締切 3分前 〜 18分前
            Main->>Fetcher: check1stBoatPopularity()
            Fetcher->>Web: 直前オッズ取得
            Web-->>Fetcher: オッズデータ
            
            alt 1号艇が単勝1番人気でない
                Fetcher-->>Main: False
                Main->>Notifier: sendNotification()
                Notifier->>Discord: 波乱レース通知送信
            else 1号艇が1番人気
                Fetcher-->>Main: True
                Note over Main: 通知スキップ
            end
        else 対象外の時間
            Note over Main: スキップ
        end
    end

    Note over Main: 処理終了
```

## 3. ファイル役割一覧

| ファイル名 | 役割 | 主なクラス/関数 |
| :--- | :--- | :--- |
| `check_races_batch.py` | **実行のエントリーポイント**。<br>時間の判定と全体の指揮を行う。 | `check_and_notify()` |
| `schedule_fetcher.py` | **データ取得担当**。<br>公式サイトからスケジュールやオッズを取得・解析する。 | `ScheduleFetcher`<br>`fetchAllSchedules()`<br>`check1stBoatPopularity()` |
| `race_notifier.py` | **通知担当**。<br>Discordへのメッセージ送信を行う。 | `RaceNotifier`<br>`sendNotification()` |
| `.github/workflows/boatrace_monitor.yml` | **インフラ設定**。<br>Python環境の構築とスクリプト実行を定義。 | - |

## 4. メンテナンスガイド

### 通知条件を変えたい場合
`scripts/check_races_batch.py` の以下の定数を変更してください。
- `MIN_OFFSET`: 何分前から検知するか（現在: 3）
- `MAX_OFFSET`: 何分先まで検知するか（現在: 18）

### オッズ条件を変えたい場合
`scripts/schedule_fetcher.py` の `check1stBoatPopularity` メソッドを改造するか、新しい判定メソッドを追加してください。
