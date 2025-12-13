# Googleスプレッドシート連携 設定ガイド

GitHub ActionsからGoogleスプレッドシートにログを保存するために、以下の手順でGoogle Cloudの設定と認証情報の取得を行ってください。

## 1. Google Cloud プロジェクトの作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセスします。
2. 左上のプロジェクト選択ドロップダウンをクリックし、「新しいプロジェクト」を作成します。
   - プロジェクト名: `BoatRaceMonitor` (任意)

## 2. APIの有効化

1. 左メニューの「APIとサービス」 > 「ライブラリ」を選択します。
2. 以下の2つのAPIを検索し、「有効にする」をクリックします。
   - **Google Sheets API**
   - **Google Drive API** (スプレッドシートの操作に必要)

## 3. サービスアカウントの作成とキー取得

1. 左メニューの「APIとサービス」 > 「認証情報」を選択します。
2. 「認証情報を作成」 > 「サービスアカウント」をクリックします。
3. 詳細を入力:
   - サービスアカウント名: `monitor-bot` (任意)
   - 「作成して続行」をクリック。
   - ロール: 「編集者」を選択し、「続行」 > 「完了」。
4. 作成されたサービスアカウントのメールアドレス（例: `monitor-bot@...iam.gserviceaccount.com`）をコピーしておきます（後で使います）。
5. 作成されたサービスアカウントをクリックし、「キー」タブを選択します。
6. 「鍵を追加」 > 「新しい鍵を作成」 > 「JSON」を選択し、「作成」をクリックします。
   - **JSONファイルが自動的にダウンロードされます。このファイルは誰にも渡さないでください。**

## 4. スプレッドシートの準備

1. [Googleスプレッドシート](https://docs.google.com/spreadsheets/) で新しいシートを作成します。
2. シートの名前（例: `BoatRaceLog`）を付けます。
3. 右上の「共有」ボタンをクリックします。
4. **手順3-4でコピーしたサービスアカウントのメールアドレス** を入力し、「編集者」として招待（送信）します。
5. ブラウザのアドレスバーから、スプレッドシートの **ID** をコピーします。
   - URL例: `https://docs.google.com/spreadsheets/d/`**`1a2b3c4d5e6f...`**`/edit`
   - この `1a2b3c4d5e6f...` の部分がシートIDです。

## 5. GitHub Secrets への登録

1. GitHubリポジトリページに行き、「Settings」 > 「Secrets and variables」 > 「Actions」を選択します。
2. 「New repository secret」をクリックし、以下の2つを登録します。

   - **Name**: `GOOGLE_SHEETS_CREDENTIALS`
     - **Secret**: ダウンロードしたJSONファイルの中身をすべてコピーして貼り付けます。
   
   - **Name**: `GOOGLE_SHEET_KEY`
     - **Secret**: 手順4-5でコピーしたスプレッドシートIDを貼り付けます。

これで準備完了です！次回のActions実行時から、ログがこのスプレッドシートに追記されます。
