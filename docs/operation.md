# MADO-queue 運用手順

この文書は、MADO-queue を日常的に起動・確認・停止・復旧する人向けの運用メモです。実装変更ではなく、現状のコードと設定から確認できる運用を整理しています。

## 通常運用手順

### 1. 起動

Docker 利用時は次を実行します。

```bash
docker compose up --build
```

起動後、次の画面を必要な端末で開きます。

| 端末 | URL | 用途 |
| --- | --- | --- |
| 発券用タブレット | `http://<サーバーIP>:8000/` | 来庁者が番号を発券します。 |
| 職員 PC | `http://<サーバーIP>:8000/processing` | 呼び出し、完了、不在、削除を操作します。 |
| 待合室表示 PC | `http://<サーバーIP>:8000/display` | 呼び出し中番号と待ち人数を表示します。 |

`localhost` はサーバー自身からアクセスする場合の表記です。他端末からアクセスする場合は、サーバーの IP アドレスに置き換えます。

### 2. 開庁中の確認

- 発券画面で番号が表示されること。
- プリンターからチケットが出ること。カテゴリ D は印刷されません。
- 職員処理画面に待ち一覧が表示されること。
- 呼び出し後、表示画面に番号が出ること。
- 表示画面の音声は、ブラウザの制約により初回クリックで有効化されます。

### 3. 停止

フォアグラウンドで起動している場合は、起動中のターミナルで `Ctrl+C` を押します。

Compose のコンテナを明示的に停止する場合は次を使います。

```bash
docker compose down
```

## 初回セットアップ

### Docker 環境

1. Docker / Docker Compose を利用できる状態にします。
2. リポジトリを取得します。
3. `docker compose up --build` を実行します。
4. 初回起動時に `entrypoint.sh` が `/data/numbers.db` の有無を確認し、存在しなければ `init_db.py` を実行します。
5. ホスト側には `./data/numbers.db` として DB が残ります。

### Python 直接実行環境

```bash
pip install -r requirements.txt
python init_db.py
python app.py
```

本番相当の起動は次です。

```bash
waitress-serve --host=0.0.0.0 --port=8000 app:app
```

## よく使うコマンド

| 目的 | コマンド |
| --- | --- |
| Docker 起動 | `docker compose up --build` |
| Docker 停止 | `docker compose down` |
| DB 初期化 | `python init_db.py` |
| 既存 DB 移行 | `python safe_migrate_db.py` |
| ローカル開発サーバー | `python app.py` |
| Waitress 起動 | `waitress-serve --host=0.0.0.0 --port=8000 app:app` |
| テスト | `python -m unittest test_app -v` |
| トップページ確認 | `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/` |
| 発券 API 確認 | `curl -s -X POST http://localhost:8000/get_next_number -H "Content-Type: application/json" -d '{"category":"A","buttonText":"住民票","timestamp":"2026-06-11T09:00:00+09:00"}'` |
| 表示 API 確認 | `curl -s http://localhost:8000/display_data` |

## トラブルシュート

### 画面が開けない

確認すること:

1. コンテナまたは Flask プロセスが起動しているか。
2. ポート 8000 が使われているか。
3. 他端末からアクセスする場合、`localhost` ではなくサーバー IP を使っているか。
4. WSL 環境では、フォアグラウンド起動で WSL セッションが生きているか。

### 番号は出るが印刷されない

確認すること:

1. カテゴリ D ではないか。カテゴリ D は仕様上印刷しません。
2. サーバーにプリンターが USB 接続されているか。
3. Docker / Linux では `PRINTER_VID` / `PRINTER_PID` が実機と一致しているか。
4. Docker で実機 USB を使う場合、`docker-compose.yml` の `devices` 設定が必要か。
5. Windows では `PRINTER_NAME` と OS 上のプリンター名が一致しているか。
6. ログに `[print_ticket] error: ...` が出ていないか。

現行実装では、印刷失敗時も発券 API は成功し、DB に発券ログが残る可能性があります。

### 待ち一覧に表示されない

確認すること:

1. 発券ログが本日分か。
2. カテゴリ D ではないか。待ち一覧はカテゴリ D を除外します。
3. 既に `processing_logs` に `processing`, `completed`, `deleted` の行がないか。
4. 日付・タイムゾーンが期待どおりか。

### 表示画面に呼び出し番号が出ない

確認すること:

1. 職員画面で「呼び出し」を押して `processing` 状態になっているか。
2. `/display_data` が `calling` を返しているか。
3. 表示側では呼び出しから 60 秒以内・最大 5 件の表示制御があります。
4. 音声は初回クリックで有効化する必要があります。

### DB をリセットしたい

運用データを消す操作なので、必要に応じて `data/numbers.db` をバックアップしてから実行してください。

```bash
docker compose down
cp data/numbers.db data/numbers.db.backup.$(date +%Y%m%d%H%M%S)
rm data/numbers.db
docker compose up --build
```

## ログ・出力・成果物の確認方法

| 対象 | 確認方法 |
| --- | --- |
| アプリログ | Docker 起動中の標準出力、または `docker compose logs`。 |
| 印刷エラー | 標準出力の `[print_ticket] error: ...`。 |
| SQLite DB | `data/numbers.db`。本番相当データなので直接編集は避けます。 |
| 発券ログ | `event_logs` テーブル。 |
| 処理ログ | `processing_logs` テーブル。 |
| 番号カウンター | `numbers` テーブル。 |

## 変更時に確認すべき点

| 変更対象 | 確認項目 |
| --- | --- |
| ボタン名・カテゴリ | `templates/index.html` の表示、`buttonText`、カテゴリ、運用要件との整合。 |
| 番号帯 | `config.py`、`docs/REQUIREMENTS.md`、実装の上限 enforcement の有無。 |
| DB スキーマ | `init_db.py` と `safe_migrate_db.py` の両方の整合。 |
| API 変更 | `app.py`、`static/script.js`、`templates/syori.html`、`templates/display.html`、テスト。 |
| プリンター変更 | `PRINTER_NAME`、`PRINTER_VID`、`PRINTER_PID`、OS / Docker の USB 設定。 |
| タイムゾーン | フロントエンド JST、バックエンドローカル時刻、SQLite `localtime`。 |
| Docker 変更 | `Dockerfile`、`docker-compose.yml`、`entrypoint.sh`、DB 永続化パス。 |
| 運用手順変更 | README、`docs/operation.md`、`docs/DEVELOPMENT.md`。 |

## 要確認として残る運用ルール

- 正式なバックアップ頻度と保存先。
- 障害時に紙チケットを再発行するか、手書き対応するか。
- 閉庁後・日跨ぎ・休日明けのリセット確認手順。
- 本番で使うプリンター機種と予備機の設定値。
- 認証なしの管理画面をどのネットワーク範囲に公開するか。
