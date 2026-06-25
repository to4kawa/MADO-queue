# MADO-queue

MADO-queue は、北海道芽室町の住民窓口で運用されている MADO（Memuro Agile Desk Open）の `queue` パッケージです。来庁者向けの番号発券、職員向けの呼び出し・処理管理、待合室向けの番号表示を、Flask と SQLite で構成する小規模自治体向けの窓口番号発券システムです。

> この README は、このリポジトリを初めて触る開発者が最短で構成と運用を把握できるように、既存ドキュメントと実装から確認できる事実を整理したものです。業務要件の詳細は [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md)、既存の実装リファレンスは [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)、開発手順は [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) も参照してください。

## 何をする repo か

- 来庁者が手続き種別を選び、カテゴリ別の番号を発券します。
- 職員が待ち一覧から番号を呼び出し、対応中・完了・不在・削除を管理します。
- 待合室のディスプレイに呼び出し中番号と待ち人数を表示します。
- 発券・処理の履歴を SQLite に保存し、待ち時間・処理時間の集計に使えるログを残します。
- USB 接続の ESC/POS レシートプリンターへチケット印刷します。カテゴリ D は印刷しません。

## 主要機能

| 機能 | 主な URL / ファイル | 概要 |
| --- | --- | --- |
| 発券画面 | `/`, `templates/index.html`, `static/script.js` | 来庁者がカテゴリ・手続きボタンを押し、`/get_next_number` で番号を発行します。 |
| 職員処理画面 | `/processing`, `templates/syori.html` | 待ち一覧と対応中一覧を表示し、呼び出し・完了・不在・削除を操作します。 |
| 表示画面 | `/display`, `templates/display.html` | `/display_data` を 3 秒ごとに取得し、呼び出し中番号と待ち人数を表示します。 |
| 採番・ログ保存 | `app.py`, `init_db.py`, `config.py` | カテゴリ別の番号開始値、発券ログ、処理ログを SQLite に保存します。 |
| DB 初期化・移行 | `init_db.py`, `safe_migrate_db.py`, `entrypoint.sh` | 初回 DB 作成と既存 DB へのカラム追加を担当します。 |
| Docker 起動 | `Dockerfile`, `docker-compose.yml` | `/data/numbers.db` を永続化し、Waitress で Flask アプリを起動します。 |

## セットアップ手順

### Docker で起動する場合（推奨）

```bash
git clone https://github.com/Memuro-Town/MADO-queue.git
cd MADO-queue
docker compose up --build
```

起動後、ブラウザで `http://localhost:8000` を開きます。初回起動時は `entrypoint.sh` が `init_db.py` を実行し、`data/numbers.db` が生成されます。

### Python で直接起動する場合

```bash
pip install -r requirements.txt
python init_db.py
python app.py
```

本番相当の WSGI サーバーで起動する場合は次を使います。

```bash
waitress-serve --host=0.0.0.0 --port=8000 app:app
```

Windows で実プリンターを使う場合は、`requirements.txt` には含まれていない `pywin32` が別途必要です。

## 実行方法

| 用途 | コマンド / URL |
| --- | --- |
| Docker 起動 | `docker compose up --build` |
| Docker 停止 | 起動中のターミナルで `Ctrl+C` |
| ローカル起動 | `python app.py` |
| Waitress 起動 | `waitress-serve --host=0.0.0.0 --port=8000 app:app` |
| テスト | `python -m unittest test_app -v` |
| 発券画面 | `http://localhost:8000/` |
| 職員処理画面 | `http://localhost:8000/processing` |
| 表示画面 | `http://localhost:8000/display` |

## ディレクトリ構成

```text
MADO-queue/
├── app.py                     # Flask アプリ本体、API、印刷、DB 操作
├── config.py                  # カテゴリごとの番号開始値
├── init_db.py                 # SQLite DB 初期化
├── safe_migrate_db.py         # 既存 DB への安全なカラム追加
├── test_app.py                # unittest ベースの API / DB テスト
├── requirements.txt           # Python 依存関係
├── Dockerfile                 # コンテナイメージ定義
├── docker-compose.yml         # Docker Compose 起動設定
├── entrypoint.sh              # コンテナ起動時の DB 初期化と Waitress 起動
├── templates/                 # Flask / Jinja2 テンプレート
├── static/                    # CSS、JavaScript、同梱 Bootstrap CSS
├── docs/                      # 要件、設計、開発、運用、監査ドキュメント
└── data/                      # 実行時 DB 保存先（Git 管理対象外の運用データ）
```

## 主要ファイルの役割

| ファイル | 役割 |
| --- | --- |
| `app.py` | 画面ルート、JSON API、採番、処理状態更新、表示データ生成、ESC/POS 印刷処理を含む中心ファイルです。 |
| `config.py` | `A=1`, `B=500`, `C=800`, `D=0` の番号開始値を定義します。 |
| `init_db.py` | `numbers`, `event_logs`, `processing_logs` テーブルを作成し、カテゴリ初期行を挿入します。 |
| `safe_migrate_db.py` | 古い DB に不足カラムを追加します。削除や破壊的変更は行わない前提のスクリプトです。 |
| `templates/index.html` | 発券ボタンと職員数ボタンを定義します。 |
| `static/script.js` | 発券 API 呼び出し、JST タイムスタンプ生成、画面表示更新を担当します。 |
| `templates/syori.html` | 職員向けの待ち・対応中一覧と API 呼び出し JavaScript を含みます。 |
| `templates/display.html` | 待合室表示、3 秒ポーリング、チャイム音生成を含みます。 |
| `Dockerfile` | Python 3.14 slim ベースで依存関係と libusb を導入します。 |
| `docker-compose.yml` | ポート `8000:8000`、`./data:/data`、プリンター VID/PID を設定します。 |

## 開発・運用時の注意点

- 実運用 DB は `numbers.db` です。テストや調査では実 DB を使わず、`DB_PATH` で一時 DB を指定してください。
- Docker では `DB_PATH=/data/numbers.db`、ホスト側では `./data/numbers.db` に永続化されます。
- レシートプリンターは Windows では `win32print`、Linux / Docker では `pyusb` を使います。
- `print_ticket()` は印刷失敗をログ出力して処理を継続する実装です。発券 API の成功と印刷成功は同義ではありません。
- カテゴリ A/B/C/D の開始値は `config.py` にありますが、番号帯の上限 enforcement は別途確認が必要です。
- CORS は `CORS_ORIGINS` 環境変数で指定できます。未指定時は `http://localhost:8000` です。
- `safe_migrate_db.py` は既存 DB の不足カラム追加用です。新規 DB のスキーマは `init_db.py` を確認してください。
- 既存監査方針では、プロダクション挙動の変更よりも証拠収集・再現テスト・文書化を優先します。

## 未確認事項

- 本番環境で使われている正確な OS、プリンタードライバー、USB 権限設定。
- カテゴリ A=1–499、B=500–799 の上限を実装で厳密に止める必要があるかどうか。
- `safe_migrate_db.py` で移行した古い DB と `init_db.py` で作った新規 DB の差分が、現行運用上どこまで許容されるか。
- カテゴリ・ボタン名・職員数の値が自治体ごとにどの程度変更される想定か。
- ログの保存期間、バックアップ頻度、障害時復旧手順の正式な運用ルール。

## 関連ドキュメント

- [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md): 業務要件・対象ユーザー・機能要件
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): 既存の実装リファレンス
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): 開発・テスト・WSL 注意点
- [docs/architecture.md](docs/architecture.md): 今回の文書化作業で整理した全体構成
- [docs/operation.md](docs/operation.md): 通常運用・初回セットアップ・トラブルシュート
- [docs/documentation-process.md](docs/documentation-process.md): 他 repo にも転用できる文書化プロセス

## License

MIT License — Copyright (c) Memuro Town

詳細は [LICENSE](LICENSE) を参照してください。

## MADO 全体の文脈

MADO は、北海道芽室町が開発・運用している行政窓口業務支援システムの OSS 版です。中・大規模向け SaaS ではなく、小規模自治体が現場で使い続けられる LITE 版として設計されている、という説明が既存 README にありました。

この `queue` リポジトリは、MADO のうち番号発券を担当する最初の公開パッケージです。既存 README では、`hub` / `form` / `care` / `move` は別リポジトリとして順次公開予定と説明されていました。これらのパッケージの公開状況や予定日は変わる可能性があるため、導入判断時には最新情報を確認してください。

## Contributing

バグ報告、ドキュメント修正、設計議論は歓迎されています。貢献前に [CONTRIBUTING.md](CONTRIBUTING.md)、行動規範は [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)、脆弱性報告は [SECURITY.md](SECURITY.md) を確認してください。

導入自治体に関する情報は [FORKED_SITES.md](FORKED_SITES.md) を参照してください。
