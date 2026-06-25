# MADO-queue アーキテクチャ整理

この文書は、既存の `docs/ARCHITECTURE.md` を置き換えるものではなく、初見の開発者が全体像を把握するために、コード・設定・既存ドキュメントから読み取れる事実を再構成したものです。

## 全体構成

MADO-queue は Flask アプリケーション 1 プロセスと SQLite 1 ファイルを中心に構成されています。画面は Flask の Jinja2 テンプレートで返され、発券・処理操作・表示更新は JSON API を呼び出します。

```text
[来庁者タブレット]
  └─ GET /, POST /get_next_number
        ↓
[Flask app.py] ── [SQLite numbers.db]
        ↓
[USB ESC/POS プリンター]

[職員 PC]
  └─ GET /processing, POST /start_processing, /end_processing, /cancel_processing, /delete_ticket
        ↓
[Flask app.py] ── [SQLite numbers.db]

[待合室ディスプレイ]
  └─ GET /display, GET /display_data（3秒ごと）
        ↓
[Flask app.py] ── [SQLite numbers.db]
```

## 処理の流れ

### 1. 発券

1. 来庁者が `/` のボタンを押します。
2. `static/script.js` がカテゴリ、ボタン名、タイムスタンプ、職員数を `/get_next_number` に POST します。
3. `app.py` が `numbers` テーブルのカテゴリ別カウンターを読み、必要に応じて日次リセットします。
4. 新しい番号を `numbers` に保存し、`event_logs` に発券ログを追加します。
5. カテゴリ D 以外では `print_ticket()` が ESC/POS データを作り、プリンターへ送信します。
6. API は `category` と `next_number` を返します。

### 2. 呼び出し開始

1. 職員が `/processing` の待ち一覧から「呼び出し」を押します。
2. `templates/syori.html` の JavaScript が `/start_processing` に POST します。
3. `app.py` が `processing_logs` に `status='processing'` の行を追加します。
4. 待ち時間は発券時刻と処理開始時刻から分単位で計算されます。

### 3. 処理完了

1. 職員が対応中一覧の「完了」を押します。
2. `/end_processing` が本日分かつ `status='processing'` の `processing_logs` を探します。
3. `end_time`, `processing_time`, `status='completed'` に更新します。

### 4. 不在・キャンセル

1. 職員が「不在」を押します。
2. `/cancel_processing` が本日分かつ `status='processing'` の `processing_logs` を削除します。
3. 待ち一覧は `event_logs` に存在し、処理ログが存在しないチケットを表示するため、対象番号は待ち状態に戻ります。

### 5. 削除

1. 職員が待ち一覧の「削除」を押します。
2. `/delete_ticket` が `processing_logs` に `status='deleted'` の行を追加します。
3. 待ち一覧の除外条件に該当するため、対象番号は待ち一覧から消えます。

### 6. 待合室表示

1. `/display` が表示用 HTML を返します。
2. ブラウザが `/display_data` を 3 秒ごとに取得します。
3. API は本日 `processing` の呼び出し中番号と、未処理チケット数を返します。
4. 表示側 JavaScript が最大件数や 60 秒以内表示、チャイム再生を制御します。

## 主要コンポーネント

| コンポーネント | ファイル | 確認できる責務 |
| --- | --- | --- |
| Flask アプリ | `app.py` | ルーティング、API、DB 操作、印刷処理、入力検証。 |
| DB 初期化 | `init_db.py` | 3 テーブル作成、カテゴリ初期値投入。 |
| DB 移行 | `safe_migrate_db.py` | 既存 DB への不足カラム追加。 |
| カテゴリ設定 | `config.py` | カテゴリ別の開始番号。 |
| 発券 UI | `templates/index.html`, `static/script.js`, `static/style.css` | ボタン定義、発券 API 呼び出し、結果表示。 |
| 職員 UI | `templates/syori.html` | 待ち・対応中一覧、操作 API 呼び出し、自動更新。 |
| 表示 UI | `templates/display.html` | 呼び出し番号表示、待ち人数表示、チャイム、ポーリング。 |
| Docker | `Dockerfile`, `docker-compose.yml`, `entrypoint.sh` | コンテナ構築、DB 永続化、Waitress 起動。 |
| テスト | `test_app.py` | Flask client と一時 DB を使った挙動確認。 |

## データや設定の流れ

### データベース

- `numbers`: カテゴリごとの現在番号と最終更新日を保持します。
- `event_logs`: 発券ごとのカテゴリ、ボタン名、時刻、番号、職員数を保持します。
- `processing_logs`: 呼び出し・完了・削除の状態、待ち時間、処理時間、発券ログ参照を保持します。

Docker 実行時は `DB_PATH=/data/numbers.db` です。Compose では `./data:/data` がマウントされるため、ホスト側の `data/numbers.db` が永続データになります。Python 直接実行時は、`DB_PATH` 未指定ならリポジトリ直下の `numbers.db` が使われます。

### 設定

| 設定 | 場所 | 内容 |
| --- | --- | --- |
| `CATEGORY_START` | `config.py` | A/B/C/D の開始番号。 |
| `DB_PATH` | 環境変数、`Dockerfile`, `entrypoint.sh` | SQLite DB のパス。 |
| `PRINTER_NAME` | 環境変数 | Windows のプリンター名。 |
| `PRINTER_VID` / `PRINTER_PID` | 環境変数、`docker-compose.yml` | Linux / Docker で USB プリンターを探す VID/PID。 |
| `CORS_ORIGINS` | 環境変数 | CORS 許可オリジン。未指定時は `http://localhost:8000`。 |
| `FLASK_DEBUG` | 環境変数 | `python app.py` 実行時の debug 有効化。 |

## 外部依存

| 種別 | 依存 | 用途 |
| --- | --- | --- |
| Python | Flask | Web アプリケーション。 |
| Python | Flask-Cors | CORS 設定。 |
| Python | waitress | 本番相当の WSGI サーバー。 |
| Python | pyusb | Linux / Docker で USB プリンターへ送信。 |
| Windows 任意 | pywin32 | Windows プリンターへ RAW 送信。 |
| OS パッケージ | libusb-1.0-0 | pyusb の実行に必要。 |
| フロントエンド | Bootstrap 4.5.2 CSS | 発券・処理画面のスタイル。 |
| ハードウェア | ESC/POS レシートプリンター | 物理チケット印刷。 |
| DB | SQLite | 単体ファイル DB。 |

## 設計上の前提

- 受付ネットワーク内での独立運用を前提としています。
- 住民の個人情報は保持しない設計です。
- サーバーに USB プリンターが接続され、ブラウザからの発券操作をサーバーが印刷へ変換します。
- カテゴリ D は来庁者カウント用途で、印刷しません。
- 番号は日次リセットされる想定です。
- 表示画面と処理画面はポーリングや自動リロードで最新状態に近づけます。WebSocket 等は使っていません。
- SQLite への同時発券では `BEGIN IMMEDIATE` により採番前に書き込みロックを取得する実装です。

## 属人化している可能性がある箇所

| 箇所 | 属人化の可能性 | 文書化・確認するとよいこと |
| --- | --- | --- |
| ボタン名・カテゴリ分類 | 芽室町の窓口運用に依存している可能性があります。 | 自治体ごとの変更ルール、カテゴリ分類基準、番号帯の意味。 |
| プリンター設定 | 機種、OS、USB 権限、ドライバー名に依存します。 | 動作確認済み機種、Windows / Docker それぞれの設定手順。 |
| 日次リセット | サーバーのローカル時刻とフロントエンド JST 生成が混在します。 | 本番サーバーのタイムゾーン、閉庁後・日跨ぎ運用。 |
| DB 運用 | `numbers.db` のバックアップ・復旧・保存期間がコードからは決まりません。 | バックアップ頻度、復旧手順、ログ保存年限。 |
| 画面運用 | どの端末でどの画面を開くかは運用に依存します。 | タブレット、職員 PC、表示用 PC の配置と起動手順。 |
| エラー対応 | 印刷失敗時も発券 API は成功し得ます。 | 紙が出ない場合の窓口オペレーション、再印刷要否。 |
| セキュリティ | URL 分離のみで認証はありません。 | 受付ネットワークの到達範囲、端末管理、将来の認証要否。 |

## コード・設定から確認できること / 推測に留めること

### コード・設定から確認できること

- Flask、SQLite、Waitress、pyusb を使っています。
- Docker では `/data/numbers.db` を永続 DB として使います。
- カテゴリ D は印刷をスキップします。
- 印刷処理は例外を捕捉してログ出力し、発券処理自体は継続します。
- `/display_data` は呼び出し中リストと待ち人数を返します。

### 推測に留めること

- 本番プリンターの現在の接続方式・権限設定。
- 各カテゴリの業務上の厳密な境界。
- ログをどの期間保存するか。
- 認証なし運用が全導入先で許容されるか。
