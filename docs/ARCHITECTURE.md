# MADO queue — Architecture

> 番号発券パッケージ `queue` の構成・API・データ構造・印刷をまとめた実装リファレンス。

> コントリビューター・開発者向けの実装リファレンスです。業務上の目的・要件は [REQUIREMENTS.md](REQUIREMENTS.md) を参照してください。変更履歴は Git のコミット履歴を正とします。

---

## 1. システム構成

### 1.1 技術スタック

| 区分 | 使用技術 | 詳細 |
|-----|---------|------|
| バックエンド | Python + Flask | Webアプリケーションフレームワーク |
| フロントエンド | HTML5 + CSS3 + JavaScript | バニラJS、Bootstrap 4.5.2 |
| データベース | SQLite | `data/numbers.db` ファイル |
| 印刷 | ESC/POS（USB接続） | Windows: `win32print` / Linux: `pyusb` で送信 |
| WSGIサーバー | Waitress | 本番環境向け |
| 実行環境 | Docker | `docker compose` での起動を標準とする |

### 1.2 ファイル構成

```
MADO-queue/
├── app.py                   # Flask メインアプリケーション
├── config.py                # カテゴリ番号開始値の定義（init_db / app で共有）
├── init_db.py               # DB初期化スクリプト
├── safe_migrate_db.py       # DBスキーママイグレーション
├── test_app.py              # テスト
├── requirements.txt         # Python 依存パッケージ
├── Dockerfile               # コンテナイメージ定義
├── docker-compose.yml       # Docker 起動設定
├── entrypoint.sh            # コンテナ起動スクリプト（初回DB初期化＋Waitress起動）
├── data/
│   └── numbers.db           # SQLiteデータベース（実行時生成）
├── static/
│   ├── script.js            # 発券画面クライアントスクリプト
│   └── style.css            # タブレット向けスタイルシート
├── templates/
│   ├── index.html           # 発券画面テンプレート
│   ├── display.html         # 公開表示画面テンプレート
│   └── syori.html           # 職員処理管理画面テンプレート
└── docs/
    ├── REQUIREMENTS.md
    └── ARCHITECTURE.md（本ファイル）
```

### 1.3 サーバー設定

| 項目 | 設定値 |
|-----|-------|
| ホスト | 0.0.0.0（全インターフェース） |
| ポート | 8000 |
| 起動コマンド | `waitress-serve --host=0.0.0.0 --port=8000 app:app` |
| CORS | 全ドメイン許可（flask-cors デフォルト設定） |

---

## 2. データベース仕様

### 2.1 テーブル: `numbers`

番号カウンターの現在値を管理するテーブル。

| カラム名 | 型 | 説明 |
|---------|---|------|
| category | CHAR(1) PRIMARY KEY | カテゴリ識別子（A/B/C/D） |
| current_number | INTEGER | 現在の番号カウンター値 |
| timestamp | DATE | 最終更新日（YYYY-MM-DD） |

**初期データ:**

| category | current_number | 備考 |
|---------|---------------|------|
| A | 1 | 1から連番 |
| B | 500 | 500から連番 |
| C | 800 | 800から連番 |
| D | 0 | 印刷なし |

### 2.2 テーブル: `event_logs`

発行された全チケットを記録するテーブル。

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | INTEGER PRIMARY KEY | NO | 自動採番 |
| category | CHAR(1) | NO | カテゴリ識別子 |
| button_text | TEXT | YES | 手続き種別名 |
| timestamp | TEXT | NO | 発行日時（ISO8601） |
| current_number | INTEGER | NO | 発行された番号 |
| staff_count | INTEGER | YES | 発行時の職員数 |

### 2.3 テーブル: `processing_logs`

チケットの処理ライフサイクルを記録するテーブル。

| カラム名 | 型 | NULL | 説明 |
|---------|---|------|------|
| id | INTEGER PRIMARY KEY | NO | 自動採番 |
| ticket_number | INTEGER | NO | 処理対象の番号 |
| category | CHAR(1) | YES | カテゴリ識別子 |
| button_text | TEXT | YES | 手続き種別名 |
| start_time | TEXT | YES | 処理開始日時（ISO8601） |
| end_time | TEXT | YES | 処理終了日時（ISO8601） |
| wait_time | INTEGER | YES | 待ち時間（分） |
| status | TEXT | NO | 状態（processing / completed / deleted） |
| processing_time | INTEGER | YES | 処理時間（秒） |
| created_at | TEXT | NO | レコード作成日時（ISO8601） |
| staff_count | INTEGER | YES | 処理時の職員数 |
| event_log_id | INTEGER | YES | event_logs.id への外部参照 |

---

## 3. API仕様

### 3.1 画面ルート

| URL | メソッド | 説明 |
|-----|---------|------|
| `/` | GET | 発券画面（index.html）を返す |
| `/processing` | GET | 処理管理画面（syori.html）を返す |
| `/display` | GET | 公開表示画面（display.html）を返す |

### 3.2 データAPI

#### POST `/get_next_number`

番号を発行し、物理チケットを印刷する。

**リクエスト（JSON）:**
```json
{
  "category": "A",
  "buttonText": "住民票",
  "timestamp": "2026-03-23T09:00:00+09:00",
  "staffCount": 3
}
```

| フィールド | 型 | 必須 | 説明 |
|---------|---|------|------|
| category | string | YES | カテゴリ識別子（A/B/C/D） |
| buttonText | string | YES | 手続き種別名 |
| timestamp | string | YES | タイムスタンプ（ISO8601+JST） |
| staffCount | integer | NO | 職員数（1〜7） |

**レスポンス（JSON）:**
```json
{
  "category": "A",
  "next_number": 5
}
```

**処理フロー:**
1. `numbers` テーブルから現在番号を取得
2. 日付変更チェック（`event_logs` に当日データがなければ番号リセット）
3. 番号をインクリメントし `numbers` テーブルを更新
4. `event_logs` にレコードを挿入
5. カテゴリDでなければ印刷処理を実行
6. 新しい番号を返す

**番号リセット規則:**
- A: 1 にリセット
- B: 500 にリセット
- C: 800 にリセット
- D: 0 にリセット

---

#### POST `/start_processing`

チケットの呼び出し（処理開始）を記録する。

**リクエスト（JSON）:**
```json
{
  "ticket_number": 5,
  "category": "A",
  "button_text": "住民票",
  "event_log_id": 42,
  "staff_count": 3
}
```

**処理フロー:**
1. `event_logs` から発行時刻を取得
2. 待ち時間を計算（現在時刻 - 発行時刻、分単位）
3. `processing_logs` に status='processing' でレコードを挿入

**レスポンス:** `{"status": "success"}`

---

#### POST `/end_processing`

処理完了を記録する。

**リクエスト（JSON）:**
```json
{
  "processing_id": 10
}
```

**処理フロー:**
1. `processing_logs` の該当レコードを取得
2. 処理時間を計算（現在時刻 - start_time、秒単位）
3. end_time, processing_time を更新し status='completed' に変更

**レスポンス:** `{"status": "success"}`

---

#### POST `/cancel_processing`

呼び出し済みチケットを待ち状態に戻す（不在対応）。

**リクエスト（JSON）:**
```json
{
  "processing_id": 10
}
```

**処理フロー:**
1. `processing_logs` から該当レコードを削除

**レスポンス:** `{"status": "success"}`

---

#### POST `/delete_ticket`

チケットを削除する。

**リクエスト（JSON）:**
```json
{
  "ticket_number": 5,
  "category": "A",
  "event_log_id": 42
}
```

**処理フロー:**
1. `processing_logs` に status='deleted' でレコードを挿入

**レスポンス:** `{"status": "success"}`

---

#### GET `/display_data`

公開表示画面向けのデータを返す。

**レスポンス（JSON）:**
```json
{
  "calling": [
    {
      "number": 5,
      "category": "A",
      "seconds_since": 15
    }
  ],
  "waiting_count": 8
}
```

| フィールド | 説明 |
|---------|------|
| calling | 本日の対応中（status='processing'）チケットのリスト。`start_time` 昇順 |
| calling[].number | 呼び出し中の番号 |
| calling[].seconds_since | 呼び出し開始からの経過秒数 |
| waiting_count | 本日の未処理チケット件数（カテゴリDを除く） |

> このAPIは当日の対応中チケットを全件返す。「呼び出しから60秒以内のみ・最大5件」の絞り込みは表示画面（display.html）側で行う。

---

## 4. 画面仕様

### 4.1 発券画面（index.html）

**URL:** `http://[サーバーIP]:8000/`
**対象端末:** タブレット端末（窓口入口に設置）
**接続プリンター:** USB接続のESC/POS対応レシートプリンター（MUNBYN POS-80C で動作確認）
**フレームワーク:** Bootstrap 4.5.2

#### 画面構成

```
┌─────────────────────────────────┐
│    職員数ボタン（1〜7）          │
├─────────────────────────────────┤
│  カテゴリA（青）  │ カテゴリB（グレー） │
│  住民票          │ 転出             │
│  戸籍謄本/抄本   │ 転入             │
│  印鑑証明        │ マイカ受取        │
│  らくらく証明     │  ...             │
│  現況届          │                 │
├─────────────────────────────────┤
│  カテゴリC（緑）                │
│  戸籍届出 │ 年金 │ おくやみ │...   │
├─────────────────────────────────┤
│  カテゴリD                     │
│  窓口以外の来庁者               │
└─────────────────────────────────┘
```

#### 操作フロー

1. 職員数ボタン（1〜7）を選択（任意）
2. 手続き種別ボタンをタップ
3. APIレスポンスを受け取り画面に番号表示
4. バイブレーションフィードバック（モバイル端末）

#### JavaScript処理（script.js）

- `issueTicket(category, buttonText)`: 番号発行処理
  - `POST /get_next_number` を呼び出し
  - レスポンスの番号を画面に表示
  - 発行完了後、選択をリセット
- タイムスタンプはJST（+09:00）で生成

---

### 4.2 職員処理管理画面（syori.html）

**URL:** `http://[サーバーIP]:8000/processing`
**対象端末:** PC ブラウザ
**実装:** Jinja2 テンプレート（サーバーサイドレンダリング）

#### 画面構成

```
┌──────────────────┬──────────────────┐
│  呼び出し待ち    │  対応中          │
├──────────────────┼──────────────────┤
│ [番号] [種別]   │ [番号] [種別]   │
│ 経過時間 XX分   │ 開始時刻 HH:MM  │
│ 発行時刻 HH:MM  │                  │
│ [呼び出し][削除] │ [不在][完了]    │
│ ...             │ ...              │
└──────────────────┴──────────────────┘
```

#### 表示ロジック

**呼び出し待ちリスト条件:**
- `event_logs` に本日のレコードが存在する
- カテゴリDを除く
- `processing_logs` に processing / completed / deleted の状態のレコードが存在しない

**対応中リスト条件:**
- `processing_logs.status = 'processing'`

#### ボタン動作

| ボタン | API | 動作 |
|------|-----|------|
| 呼び出し（処理開始） | POST /start_processing | 待ちリストから対応中に移動 |
| 削除 | POST /delete_ticket | 待ちリストから削除（確認ダイアログあり） |
| 不在（待ちに戻す） | POST /cancel_processing | 対応中から待ちリストに戻す |
| 完了（処理終了） | POST /end_processing | 対応中から完了済みに移動（確認ダイアログあり） |

#### 自動更新

- 10秒間隔で自動リロード
- ユーザー操作後5秒間は更新を停止（誤操作防止）

---

### 4.3 公開表示画面（display.html）

**URL:** `http://[サーバーIP]:8000/display`
**対象端末:** 32インチ以上の大型ディスプレイ（PC接続）
**実装:** バニラJS + CSS アニメーション

#### 画面構成

```
┌───────────────────────────────────────┐
│ 住民窓口 番号案内         [時計表示] │
├───────────────────────────────────────┤
│           呼び出し中                  │
│  ┌───────────┐  ┌───────────┐        │
│  │ カテゴリ A │  │ カテゴリ B │        │
│  │   【 5 】  │  │  【545】  │        │
│  │番号札をお持ちの方│              │
│  └───────────┘  └───────────┘        │
├───────────────────────────────────────┤
│  お待ちの方              【8】人      │
├───────────────────────────────────────┤
│ 番号が呼ばれましたら、担当窓口へ...   │
└───────────────────────────────────────┘
```

#### 表示仕様

| 項目 | 仕様 |
|-----|------|
| 更新間隔 | 3秒（`/display_data` API ポーリング） |
| 呼び出し表示 | 最大5件まで。呼び出しから60秒以内のみ表示 |
| 番号フォントサイズ | 111px（超大型表示） |
| チャイム | 新規呼び出し検出時に Web Audio API で合成音を再生 |
| チャイム有効化 | 初回クリックで有効化（ブラウザのセキュリティポリシー対応） |
| アニメーション | 呼び出し中カードは点滅エフェクト |

#### チャイム仕様

Web Audio API のサイン波オシレーターを使用した合成チャイム音。

| パラメーター | 値 |
|------------|---|
| 音色 | サイン波（sine） |
| 再生タイミング | 前回と異なる呼び出し番号セットを検出した時 |

---

## 5. 印刷仕様

### 5.0 プリンター接続方式

| 項目 | 仕様 |
|-----|------|
| 接続方式 | USB |
| プリンター機種 | ESC/POS 対応レシートプリンター（MUNBYN POS-80C で動作確認） |
| データ形式 | ESC/POS バイト列（`_build_escpos_data()` で生成） |
| 印刷API（Windows） | `win32print`：OSに登録済みのプリンター名へRAW送信 |
| 印刷API（Linux/Docker） | `pyusb`：VID/PID でUSBデバイスを特定し直接送信 |

タブレット端末のブラウザからサーバーへHTTPリクエストを送信し、サーバーが USB 接続されたレシートプリンターへ印刷指示を行う。送信するESC/POSデータは両プラットフォームで共通で、実行環境（`sys.platform`）に応じて送信経路となるAPIだけを切り替える。

> **補足:** Windows と Linux の違いは「プリンターへ命令を届けるAPI」であって、物理的な接続はどちらも USB。Bluetooth は使用しない。Windows では OS が機種ドライバを持つためプリンター名（`PRINTER_NAME`）で送り、Linux/Docker ではドライバを介さず VID/PID で直接 USB に書き込む。

---

### 5.1 チケット印刷内容

```
カテゴリ: X
用途: [手続き種別名]
日時: MM.DD-HH:MM:SS
番号: [番号]

[注記（条件付き）]
```

### 5.2 印刷設定（ESC/POS コマンド）

チケットは `app.py` の `_build_escpos_data()` でESC/POSバイト列として組み立てる。文字エンコーディングは Windows が cp932、Linux が utf-8。

| 項目 | コマンド／仕様 |
|-----|------|
| 初期化 | `ESC @` |
| 配置 | 中央揃え（`ESC a 0x01`） |
| カテゴリ・用途・日時 | 縦2倍（`GS ! 0x01`） |
| 番号 | 縦横4倍（`GS ! 0x33`） |
| 注記 | 通常サイズ（`GS ! 0x00`） |
| 用紙カット | 48ドット送り後にカット（`GS V 0x41 0x30`） |
| 印刷部数 | 2枚（自動） |

### 5.3 条件付き注記

| 条件 | 印字内容 |
|-----|---------|
| カテゴリが A 以外 | 「カテゴリAの方を先に ご案内する場合があります」 |

### 5.4 印刷スキップ条件

- カテゴリDの場合は印刷を行わない

---

## 6. 番号管理仕様

### 6.1 番号採番ルール

| カテゴリ | 初期値 | 採番方式 | リセット後 |
|---------|-------|---------|----------|
| A | 1 | +1 | 1 |
| B | 500 | +1（500〜） | 500 |
| C | 800 | +1（800〜） | 800 |
| D | 0 | +1 | 0 |

### 6.2 日次リセットロジック

```
1. GET /get_next_number 呼び出し時
2. numbers.timestamp が今日以外 かつ event_logs に当日データがない
   → numbers テーブルのカウンターをリセット
   → numbers.timestamp を今日に更新
3. それ以外は現在の番号を使用
```

- サーバー再起動後の二重リセット防止のため、`event_logs` の当日データ有無を確認する

---

## 7. タイムゾーン仕様

- すべてのタイムスタンプは **日本標準時（JST / UTC+9）** を使用
- フロントエンドで `new Date().toLocaleString('ja-JP', {timeZone: 'Asia/Tokyo'})` を使用
- バックエンドは `sqlite` の `DATE('now', 'localtime')` でローカル時刻を使用

---

## 8. エラーハンドリング

| 状況 | 処理 |
|-----|------|
| 印刷エラー | try-catchで捕捉し、ログ出力後も処理を継続（チケット発行自体は成功） |
| DB操作エラー | ログ出力、HTTPエラーレスポンス返却 |
| 存在しない処理IDへの操作 | エラーレスポンスを返却 |

---

## 9. 起動手順

### 9.1 Docker で起動（推奨）

```bash
docker compose up --build
```

初回起動時に `entrypoint.sh` が DB を自動初期化し、`data/numbers.db` を生成する。

### 9.2 ローカルで起動（Docker を使わない場合）

```bash
pip install -r requirements.txt
python init_db.py                                   # 初回のみ（DB初期化）
python app.py                                       # 開発サーバー
waitress-serve --host=0.0.0.0 --port=8000 app:app   # 本番起動（Waitress）
```

### 9.3 スキーママイグレーション（バージョンアップ時）

```bash
python safe_migrate_db.py
```

### 9.4 プリンター設定（環境変数）

| 環境変数 | 既定値 | 説明 |
|---------|-------|------|
| `PRINTER_NAME` | `POS-80C (copy 1)` | Windows で使用するプリンター名 |
| `PRINTER_VID` | `0x04b8` | USBベンダーID（Linux/pyusb で使用） |
| `PRINTER_PID` | `0x0e20` | USBプロダクトID（Linux/pyusb で使用） |

---

## 10. アクセスURL一覧

| 画面 | URL | 利用者 |
|-----|-----|-------|
| 発券画面 | `http://[サーバーIP]:8000/` | 来庁者（タブレット） |
| 処理管理画面 | `http://[サーバーIP]:8000/processing` | 窓口職員（PC） |
| 公開表示画面 | `http://[サーバーIP]:8000/display` | 待合エリア（大型モニター） |

---

## 11. 依存パッケージ

| パッケージ | バージョン | 用途 |
|---------|----------|------|
| Flask | >=3.0.0 | Webフレームワーク |
| Flask-Cors | >=4.0.0 | CORS対応 |
| waitress | >=3.0.0 | WSGIサーバー |
| pyusb | >=1.0.0 | USB印刷（Linux/Docker） |
| pywin32 | — | Windows印刷API（Windows環境のみ） |

---

## 12. 実装から確認できる全体像と要確認事項

この節は、属人化を減らすために `app.py`、`init_db.py`、`safe_migrate_db.py`、`templates/`、`static/`、Docker 関連ファイルを読み、既存の実装リファレンスへ追記したものです。設計意図として断定できる内容と、コード・文書からは確認しきれない内容を分けて扱います。

### 12.1 全体構成

- Flask アプリケーションが、発券画面、職員処理画面、公開表示画面、JSON API、印刷処理を 1 つのプロセスで提供する。
- SQLite は `data/numbers.db` を既定の保存先とし、`numbers`、`event_logs`、`processing_logs` の 3 テーブルで採番状態・発券履歴・処理履歴を管理する。
- フロントエンドは Jinja2 テンプレートとバニラ JavaScript で構成され、ビルド工程を必要としない。
- Docker 起動では `entrypoint.sh` が DB ファイルの有無を確認し、初回のみ `init_db.py` を実行した上で Waitress を起動する。

### 12.2 処理の流れ

1. 来庁者または職員が発券画面でカテゴリ・手続きボタンを選択する。
2. `static/script.js` が `/get_next_number` へ JSON を送信する。
3. `app.py` がカテゴリ別の現在番号を SQLite から取得し、必要に応じて日次リセットを行う。
4. 発券履歴を `event_logs` に保存する。
5. カテゴリ D 以外ではサーバー側の印刷処理を呼び出す。印刷失敗はログ出力されるが、発券レスポンス自体は継続される。
6. 職員処理画面は未処理の `event_logs` と `processing_logs` の状態をもとに待ち一覧・対応中一覧を表示する。
7. `/start_processing`、`/end_processing`、`/cancel_processing`、`/delete_ticket` が `processing_logs` を追加・更新・削除する。
8. 公開表示画面は `/display_data` を定期的に取得し、呼び出し中番号と待ち人数を表示する。

### 12.3 主要コンポーネント

| コンポーネント | 役割 | 確認元 |
|---|---|---|
| Flask ルート | 画面表示、採番、処理開始・完了・取消、削除、表示データ取得を提供する。 | `app.py` |
| DB 初期化 | 新規 DB 用の 3 テーブルとカテゴリ初期値を作成する。 | `init_db.py` |
| DB 移行 | 既存 DB に不足カラムを追加する。 | `safe_migrate_db.py` |
| 発券画面 | 職員数、カテゴリ、手続きボタンを表示し、採番 API を呼び出す。 | `templates/index.html`, `static/script.js` |
| 職員処理画面 | 待ち一覧・対応中一覧と操作ボタンを表示する。 | `templates/syori.html` |
| 公開表示画面 | 呼び出し中番号、待ち人数、時計、チャイムを表示する。 | `templates/display.html` |
| 印刷処理 | ESC/POS バイト列を作り、Windows では `win32print`、Linux では `pyusb` 経由で送信する。 | `app.py` |
| Docker 起動 | コンテナ起動、DB 初期化、Waitress 起動、データ永続化を担う。 | `Dockerfile`, `docker-compose.yml`, `entrypoint.sh` |

### 12.4 データと設定の流れ

- カテゴリごとの採番開始値は `config.py` の `CATEGORY_START` を `app.py` と `init_db.py` が参照する。
- プリンター設定は環境変数 `PRINTER_NAME`、`PRINTER_VID`、`PRINTER_PID` から読み込まれ、未設定時は既定値が使われる。
- `data/` は Docker Compose でホストディレクトリとしてマウントされるため、コンテナ再作成後も DB ファイルが残る。
- 発券時の `staffCount` は任意項目として `event_logs` に保存され、処理開始時に `processing_logs` へ引き継がれる。
- API の JSON スキーマは一部で camelCase（例: `buttonText`, `staffCount`）と snake_case（例: `ticket_number`, `event_log_id`）が混在する。これは現行実装の事実であり、変更する場合は互換性確認が必要。

### 12.5 外部依存

- Python パッケージは `requirements.txt` で管理される。
- UI は CDN 上の Bootstrap / jQuery / Popper を参照する画面があるため、完全オフライン運用では表示・操作への影響確認が必要。
- プリンター実機を使う場合、Windows では OS に登録されたプリンター名、Linux/Docker では USB デバイスアクセスが必要になる。
- Docker で USB プリンターを使う場合は、`docker-compose.yml` の USB デバイス設定を環境に合わせて有効化する必要がある。

### 12.6 設計上の前提

- 受付ネットワーク内での独立運用を前提とし、住民個人情報は保存しない。
- 認証・権限管理は実装されておらず、画面 URL の分離が主な利用者分離になっている。
- SQLite 単体運用を前提としているため、複数プロセス・高負荷・同時発券時の厳密な挙動は別途検証が必要。
- 印刷失敗時も採番と DB 記録を継続する実装であり、紙チケットが出ない場合の窓口運用は手順として決めておく必要がある。

### 12.7 属人化している可能性がある箇所

- 手続きボタンの文言とカテゴリ分類は、芽室町の窓口運用に依存している可能性がある。
- プリンター既定値、印字文言、2 枚印刷、カテゴリ A 優先の注意書きは、運用現場の判断が含まれている可能性がある。
- 職員数 1〜7 の選択肢、待ち人数の算出条件、表示画面の 60 秒表示・最大 5 件表示は、他自治体でそのまま適用できるとは限らない。
- 日次リセットのタイミングはサーバーのローカル時刻と `event_logs` の当日データに依存するため、運用時間外・日付跨ぎの扱いは明文化が必要。

### 12.8 不明・要確認事項

- カテゴリ A=1〜499、B=500〜799 の上限を実装で強制する必要があるかどうか。
- 発券 API で印刷失敗が起きた場合、来庁者・職員にどのように通知すべきか。
- 職員処理画面と公開表示画面に認証を追加すべきかどうか。
- 同時発券時に SQLite のロック・トランザクションで十分な一意性が確保されるかどうか。
- 既存 DB を `safe_migrate_db.py` で移行した場合と、新規 DB を `init_db.py` で作成した場合のスキーマ差分を許容するかどうか。
