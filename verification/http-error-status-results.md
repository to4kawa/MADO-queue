# HTTP error status verification results

## 対象commit SHA

`fb7198230f2a10cf28c43fba45b79147dd7ec74e`

## 実行環境

- Python: 3.14.4
- Flask: 3.1.3
- SQLite module: n/a; SQLite library: 3.45.1

## 実行コマンド

```sh
python3 verification/http_error_status_verify.py
python3 -m py_compile verification/http_error_status_verify.py
python3 -m unittest test_app -v
```

## 対象ルート一覧

- POST /get_next_number
- POST /start_processing
- POST /end_processing
- POST /cancel_processing
- POST /delete_ticket
- GET /display_data

## 正常系と異常系の結果表

| route | method | normal_status | exception | status | content_type | field | unhandled | consistent | classification | json |
|---|---|---|---|---|---|---|---|---|---|---|
| /get_next_number | POST | 200 | DB接続失敗 | 500 | application/json | error=Internal server error | False | True | 適切 | {"error": "Internal server error"} |
| /get_next_number | POST | 200 | SQL実行失敗 | 500 | application/json | error=Internal server error | False | True | 適切 | {"error": "Internal server error"} |
| /get_next_number | POST | 200 | commit失敗 | 500 | application/json | error=Internal server error | False | True | 適切 | {"error": "Internal server error"} |
| /start_processing | POST | 200 | DB接続失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /start_processing | POST | 200 | SQL実行失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /start_processing | POST | 200 | commit失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /end_processing | POST | 200 | DB接続失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /end_processing | POST | 200 | SQL実行失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /end_processing | POST | 200 | commit失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /cancel_processing | POST | 200 | DB接続失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /cancel_processing | POST | 200 | SQL実行失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /cancel_processing | POST | 200 | commit失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /delete_ticket | POST | 200 | DB接続失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /delete_ticket | POST | 200 | SQL実行失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /delete_ticket | POST | 200 | commit失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /display_data | GET | 200 | DB接続失敗 | 200 | application/json |  | False | True | 適切 | {"calling": [], "waiting_count": 0} |
| /display_data | GET | 200 | SQL実行失敗 | 200 | application/json |  | False | True | 適切 | {"calling": [], "waiting_count": 0} |

## HTTP 200で失敗JSONを返した具体例

| route | method | normal_status | exception | status | content_type | field | unhandled | consistent | classification | json |
|---|---|---|---|---|---|---|---|---|---|---|
| /start_processing | POST | 200 | DB接続失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /start_processing | POST | 200 | SQL実行失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /start_processing | POST | 200 | commit失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /end_processing | POST | 200 | DB接続失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /end_processing | POST | 200 | SQL実行失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /end_processing | POST | 200 | commit失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /cancel_processing | POST | 200 | DB接続失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /cancel_processing | POST | 200 | SQL実行失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /cancel_processing | POST | 200 | commit失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /delete_ticket | POST | 200 | DB接続失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /delete_ticket | POST | 200 | SQL実行失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |
| /delete_ticket | POST | 200 | commit失敗 | 200 | application/json | success=False | False | False | 不整合 | {"error": "Internal server error", "success": false} |

## 本家Issue候補にするべきか

本家Issue候補にするべき事実が確認された。`/start_processing`, `/end_processing`, `/cancel_processing`, `/delete_ticket` はDB内部エラー時に `success: false` と `error` を含むJSONを返す一方、HTTPステータスは200だった。

## 修正案ではなく、確認された事実だけ

- `/get_next_number` は確認したDB接続失敗、SQL実行失敗、commit失敗でHTTP 500のJSONを返した。
- `/start_processing`, `/end_processing`, `/cancel_processing`, `/delete_ticket` は確認したDB接続失敗、SQL実行失敗、commit失敗でHTTP 200の失敗JSONを返した。
- `/display_data` は確認したDB接続失敗、SQL実行失敗でHTTP 200の正常形JSON（空配列と0件）を返した。
- Flask test client上で未処理例外としてHTML 500へ到達したケースはなかった。

## 未検証事項

- 実プリンター、Docker、本番DB、実ブラウザからの挙動。
- SQLite以外のDBエラー。
- `/processing` HTMLルートおよび対象外API。
- 外部GitHub Issue #4へのコメント投稿。

## AI Assistance

- 使用ツール: OpenAI Codex
- 利用範囲: コード読解、例外注入テスト作成、実行、結果整理
- 人間による確認: 後で実施予定
