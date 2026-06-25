# コード解析に基づく既存文書への追記候補

## 目的

この文書は完成版の docs ではない。既存の `README.md`、`docs/REQUIREMENTS.md`、`docs/ARCHITECTURE.md`、`docs/DEVELOPMENT.md` を置き換えたり、文書体系を再構成したりするものではない。

目的は、コード解析から見えた「既存 docs に少量追加すると、今後のメンテナーがコードを理解しやすくなる観点」を提案として整理することである。各項目の採用、不採用、修正、表現の調整はメンテナーが判断する。

## 前提として読んだ文書

- `README.md`
- `docs/REQUIREMENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/DEVELOPMENT.md`
- その他、確認したコード・設定ファイル
  - `app.py`
  - `config.py`
  - `init_db.py`
  - `safe_migrate_db.py`
  - `templates/index.html`
  - `templates/syori.html`
  - `templates/display.html`
  - `static/script.js`
  - `static/style.css`
  - `Dockerfile`
  - `docker-compose.yml`
  - `entrypoint.sh`
  - `test_app.py`
  - `requirements.txt`

## コード解析で確認した範囲

- 主要なアプリケーション入口
  - Flask アプリケーション定義、DB パス、CORS、プリンター設定、起動条件を `app.py` で確認した。
- 主要ルート/API
  - `/`、`/processing`、`/display`、`/get_next_number`、`/start_processing`、`/end_processing`、`/cancel_processing`、`/delete_ticket`、`/display_data` を確認した。
- DB 初期化・移行
  - `init_db.py` の fresh schema、`safe_migrate_db.py` の既存 DB 向けカラム追加、`config.py` のカテゴリ開始値を確認した。
- テンプレート
  - 発券画面、処理管理画面、公開表示画面の HTML、Jinja2 変数、クライアント側 fetch 呼び出しを確認した。
- 静的ファイル
  - 発券画面の `static/script.js`、タブレット向け CSS、同梱 Bootstrap ファイルの参照方法を確認した。
- Docker/起動関連
  - Docker イメージ、Compose 設定、`entrypoint.sh` による DB 初期化と Waitress 起動を確認した。
- テスト
  - `test_app.py` の一時 DB 利用、プリンタースタブ、既存 API テストの範囲を確認した。
- 外部依存
  - Flask、Flask-Cors、Waitress、pyusb、Windows 任意依存の pywin32、Linux 側の libusb を確認した。

## ARCHITECTURE.md への追記候補

### 1. API リクエストの互換性境界

#### なぜあるとよいか

`/start_processing`、`/end_processing`、`/cancel_processing` は、ARCHITECTURE.md の現在の例では `processing_id` を中心に説明されている。一方、実際の処理管理画面は `ticket_number` を送信し、サーバー側も `ticket_number` で当日分の `processing_logs` を検索・更新・削除している。API 仕様としてどちらを正とみなすかを本文に明示すると、今後の修正時に画面・API・DB の接続関係を追いやすくなる。

#### コードから確認できた事実

- `templates/syori.html` の完了・不在ボタンは `data-number` を読み取り、`ticket_number` を JSON body に入れて `/end_processing`、`/cancel_processing` へ送信している。
- `app.py` の `/end_processing` と `/cancel_processing` は `request.json.get('ticket_number')` を必須入力として扱い、`processing_id` は参照していない。
- 対象レコードは `ticket_number`、`status='processing'`、本日分の `created_at` で絞り込まれる。

#### 既存文書のどの章に入れると自然か

`docs/ARCHITECTURE.md` の「3. API仕様」の `/end_processing`、`/cancel_processing`、および「4.2 職員処理管理画面」のボタン動作説明に入れると自然である。

#### メンテナーに確認したいこと

- 今後の API 仕様として、`processing_id` と `ticket_number` のどちらを正式な入力にするのか。
- 同一番号の処理中レコードが複数存在しうる場合に、現行の `ticket_number` 指定で十分か。
- 画面側の実装に合わせて docs を修正するのか、将来的に API を `processing_id` ベースへ寄せるのか。

#### そのまま貼れる文章案

> 職員処理管理画面からの完了・不在操作は、現在の実装では `processing_id` ではなく `ticket_number` を送信する。サーバー側は `ticket_number` と `status='processing'` に加え、`created_at` が当日のレコードに限定して更新または削除する。番号は日次リセットされるため、過去日の同番号レコードに作用しないよう日付条件を含めている。

### 2. `event_log_id` と旧形式データの共存

#### なぜあるとよいか

待ち一覧の SQL は `event_log_id` がある新形式と、`ticket_number + category` で対応する旧形式の両方に対応している。この互換性の意図を ARCHITECTURE.md に短く書いておくと、複雑な `NOT EXISTS` 条件が単なる冗長条件ではなく、既存データ互換のための設計であることが伝わる。

#### コードから確認できた事実

- `_WAITING_LIST_SQL` は `processing_logs.event_log_id = event_logs.id` を優先しつつ、`event_log_id IS NULL` の場合は `ticket_number` と `category` でも照合する。
- `safe_migrate_db.py` は既存 `processing_logs` に `event_log_id` カラムがなければ追加するが、既存行へ値を backfill していない。
- `templates/syori.html` は待ち一覧の各行から `event_log_id` を `/start_processing` と `/delete_ticket` へ送信している。

#### 既存文書のどの章に入れると自然か

`docs/ARCHITECTURE.md` の「2.3 テーブル: processing_logs」または「4.2 職員処理管理画面」の表示ロジック説明に入れると自然である。

#### メンテナーに確認したいこと

- `event_log_id` なしの旧データをどの期間までサポートする想定か。
- 将来的に `event_log_id` を必須にする予定があるか。
- 旧形式互換を残す場合、どの docs に「削除してはいけない理由」を置くのがよいか。

#### そのまま貼れる文章案

> 待ち一覧の除外判定は、`processing_logs.event_log_id` があるレコードでは `event_logs.id` で照合し、`event_log_id` がない旧形式のレコードでは `ticket_number` と `category` で照合する。これは、移行前に作成された処理ログと、`event_log_id` を持つ新しい処理ログを同じ画面で扱うための互換条件である。

### 3. 発券 API のトランザクション境界と印刷タイミング

#### なぜあるとよいか

発券処理は、DB 採番・イベントログ記録・印刷・レスポンス返却の順序が保守上重要である。特に、DB 書き込み後に印刷を行い、印刷失敗時も発券結果を返す設計は、運用判断に直結するため、ARCHITECTURE.md の印刷仕様と API 処理フローの間に境界を明示すると理解しやすい。

#### コードから確認できた事実

- `/get_next_number` は `BEGIN IMMEDIATE` で SQLite の書き込みロックを取得してから `numbers` を読み、番号を更新する。
- `event_logs` への INSERT と `numbers` の UPDATE が成功した後、DB コンテキストを抜けてから `print_ticket()` を呼ぶ。
- `print_ticket()` はカテゴリ D では何もせず、その他カテゴリでは印刷例外を捕捉してログ出力するが、API エラーにはしない。

#### 既存文書のどの章に入れると自然か

`docs/ARCHITECTURE.md` の「3.2 データAPI / POST /get_next_number」の処理フロー、または「5. 印刷仕様」に入れると自然である。

#### メンテナーに確認したいこと

- 印刷失敗時に DB に残る発券ログを、現場ではどのように扱う想定か。
- 再印刷や手書き発券などの運用手順を文書化する必要があるか。
- `BEGIN IMMEDIATE` による同時発券対策を、正式な設計仕様として記載してよいか。

#### そのまま貼れる文章案

> `/get_next_number` は SQLite の書き込みロックを取得してから採番し、`numbers` の更新と `event_logs` への記録を先に確定する。印刷は DB 書き込み後に実行されるため、プリンターエラーが発生しても発券番号とイベントログは残り、API は発券結果を返す。カテゴリ D は印刷対象外である。

### 4. CORS 設定の実装上の既定値

#### なぜあるとよいか

ARCHITECTURE.md では CORS が全ドメイン許可と説明されているが、実装では `CORS_ORIGINS` 環境変数または `http://localhost:8000` を使って origin を指定している。セキュリティ関連の説明は運用構成に影響するため、実装値に合わせて補足すると誤解を避けられる。

#### コードから確認できた事実

- `app.py` は `CORS_ORIGINS` 環境変数をカンマ区切りで読み、未指定時は `http://localhost:8000` を使用する。
- `CORS(app, origins=_cors_origins)` として Flask-Cors に渡している。

#### 既存文書のどの章に入れると自然か

`docs/ARCHITECTURE.md` の「1.3 サーバー設定」に入れると自然である。

#### メンテナーに確認したいこと

- 本番運用で想定する origin は固定か、受付ネットワーク内の複数端末を許可するのか。
- `CORS_ORIGINS` の設定例を DEVELOPMENT.md にも追加する必要があるか。

#### そのまま貼れる文章案

> CORS の許可 origin は `CORS_ORIGINS` 環境変数で指定する。未指定時は `http://localhost:8000` を許可する。複数 origin を許可する場合はカンマ区切りで指定する。

## DEVELOPMENT.md への追記候補

### 1. 一時 DB を使った手動確認手順

#### なぜあるとよいか

AGENTS.md の監査ルールでは real `numbers.db` を使わないことが重視されている。DEVELOPMENT.md にも `DB_PATH` を使った一時 DB の手動確認方法があると、開発者が本番相当データを誤って汚さずに API 動作を確認しやすい。

#### コードから確認できた事実

- `app.py`、`init_db.py`、`safe_migrate_db.py` は `DB_PATH` 環境変数を優先する。
- `test_app.py` は `tempfile.mkstemp()` で一時 DB を作り、`DB_PATH` を設定してから `init_db.py` と `app.py` を読み込む。

#### 既存文書のどの章に入れると自然か

`docs/DEVELOPMENT.md` の「4. テスト」または「5. DB のリセット」に入れると自然である。

#### メンテナーに確認したいこと

- 手動確認でも一時 DB 利用を推奨ルールとして明文化するか。
- Docker 利用時とローカル Python 利用時で、推奨する一時 DB 手順を分けるか。

#### そのまま貼れる文章案

> 本番・実運用の `numbers.db` を使わずに手動確認する場合は、`DB_PATH` に一時ファイルを指定してから `init_db.py` とアプリを起動する。`app.py` は import 時に `DB_PATH` を読むため、テストや手動スクリプトではアプリを読み込む前に環境変数を設定する。
>
> ```bash
> tmpdb=$(mktemp /tmp/mado-queue.XXXXXX.db)
> DB_PATH="$tmpdb" python init_db.py
> DB_PATH="$tmpdb" python app.py
> ```

### 2. safe migration の適用対象と限界

#### なぜあるとよいか

`safe_migrate_db.py` は既存 DB に不足カラムを追加するが、fresh schema と完全に同じ制約へ作り替えるものではない。開発者が migration を「全スキーマを正規化する処理」と誤解しないよう、適用対象と限界を DEVELOPMENT.md に置くと事故を避けやすい。

#### コードから確認できた事実

- `safe_migrate_db.py` は DB ファイルが存在しない場合は何もせず終了する。
- `ALTER TABLE ... ADD COLUMN` で `processing_logs` と `event_logs` に不足カラムを追加する。
- 既存行への `event_log_id` backfill や、制約差分の作り直しは行っていない。

#### 既存文書のどの章に入れると自然か

`docs/DEVELOPMENT.md` の「5. DB のリセット」の後、または新しい短い「既存 DB の移行」節に入れると自然である。

#### メンテナーに確認したいこと

- 本番 DB に対する `safe_migrate_db.py` の実行手順を正式に docs 化してよいか。
- 実行前バックアップを必須手順として明記するか。
- migration 後に確認すべき PRAGMA や画面動作を標準化するか。

#### そのまま貼れる文章案

> `safe_migrate_db.py` は既存 DB に不足しているカラムを追加するための補助スクリプトであり、DB 全体を fresh schema と同一に作り直すものではない。既存行への `event_log_id` の補完や制約の再定義は行わない。実運用 DB に適用する場合は、事前に `numbers.db` をバックアップしてから実行する。

### 3. プリンターなし確認時の期待ログ

#### なぜあるとよいか

DEVELOPMENT.md はプリンターなしでもテスト可能と説明しているが、手動発券ではカテゴリ D 以外で `print_ticket` のエラーログが出る可能性がある。期待されるログと DB の残り方を短く書くと、開発者がプリンター未接続による想定内エラーとアプリ異常を区別しやすい。

#### コードから確認できた事実

- Linux/Docker では `pyusb` が `PRINTER_VID` / `PRINTER_PID` に一致する USB デバイスを探す。
- 見つからない場合、`print_ticket()` は例外を捕捉して `[print_ticket] error: ...` を出力する。
- 印刷処理は DB 書き込み後に実行されるため、発券番号と `event_logs` は残る。
- カテゴリ D では `print_ticket()` が早期 return する。

#### 既存文書のどの章に入れると自然か

`docs/DEVELOPMENT.md` の「6. プリンター設定（任意）」に入れると自然である。

#### メンテナーに確認したいこと

- プリンター未接続での手動確認を、開発時の標準手順として認めるか。
- 印刷失敗時の業務手順を DEVELOPMENT.md に書くか、REQUIREMENTS.md 側へ回すか。

#### そのまま貼れる文章案

> プリンター未接続の環境でカテゴリ A/B/C を発券すると、ログに `[print_ticket] error: ...` が出る場合がある。これは印刷送信に失敗したことを示すが、DB 書き込み後に印刷する実装のため、採番結果と `event_logs` の記録は残る。カテゴリ D は印刷処理を行わない。

## REQUIREMENTS.md への追記候補

### 1. 番号帯の上限到達時の扱い

#### なぜあるとよいか

REQUIREMENTS.md はカテゴリ A を 1〜499、B を 500〜799 としている。一方、コード上の採番は開始値からインクリメントするのみで、A/B の上限到達時に停止・警告・次カテゴリへ移る処理は確認できない。これは要件と実装の関係を明確にしておくと、監査・保守時の判断がしやすい。

#### コードから確認できた事実

- `config.py` はカテゴリごとの開始値を定義している。
- `/get_next_number` は現在値に 1 を足して更新する。
- A=499、B=799 を超えた場合の拒否、警告、リセット、カテゴリ変更処理は確認できない。

#### 既存文書のどの章に入れると自然か

`docs/REQUIREMENTS.md` の「FR-002: カテゴリ管理機能」または「5. 制約事項」に入れると自然である。

#### メンテナーに確認したいこと

- A=1〜499、B=500〜799 は厳密な上限なのか、視覚的な目安の番号帯なのか。
- 上限を超える発券が起きた場合、システムで止めるべきか、現場運用で扱うべきか。
- C=800〜 と D の番号の業務上の意味をどう説明するか。

#### そのまま貼れる文章案

> カテゴリごとの番号帯は、来庁者と職員が手続き種別を識別しやすくするための開始番号として扱う。上限到達時に自動停止するか、運用で扱うかは自治体ごとの運用判断とする。上限を厳密に enforced する場合は、別途エラー処理と運用手順を定義する。

### 2. 印刷失敗時の業務上の扱い

#### なぜあるとよいか

実装では印刷失敗時も発券は成功扱いになる。これは実運用で「番号は発行済みだが紙が出ていない」状態を生むため、要件側に運用前提または未確認事項として置くと、現場判断の属人化を下げられる。

#### コードから確認できた事実

- `print_ticket()` は例外を捕捉してログを出すだけで、API レスポンスを失敗にしない。
- `/get_next_number` は DB 書き込み成功後に印刷を呼び出し、印刷結果に関係なく `category` と `next_number` を返す。
- カテゴリ D は印刷しない。

#### 既存文書のどの章に入れると自然か

`docs/REQUIREMENTS.md` の「NFR-004: 印刷」または「5. 制約事項」に入れると自然である。

#### メンテナーに確認したいこと

- 印刷失敗時、職員が番号を控えて手書きする、再発券する、DB を修正するなど、どの運用が正しいか。
- API が成功を返す現在の挙動を要件として認めるか、将来的に変更したいか。
- 印刷失敗を来庁者向け画面に表示する必要があるか。

#### そのまま貼れる文章案

> 印刷に失敗した場合でも、採番と発券ログの記録が成功していれば番号は発行済みとして扱う。紙の番号札が出ない場合の再発券、手書き対応、職員への連絡方法は、導入先の運用手順として別途定める。

### 3. 日次リセットの時刻基準

#### なぜあるとよいか

REQUIREMENTS.md は「毎日0時に自動リセット」としているが、実装は常駐ジョブではなく、発券 API 呼び出し時に日付差分と当日ログ有無を見てリセットする。要件側に「0時に即時実行されるバッチ」ではなく「次回発券時に日付を検知する」方式を明示するかどうかを確認するとよい。

#### コードから確認できた事実

- `/get_next_number` 呼び出し時に `numbers.timestamp` と今日の日付を比較する。
- 当日 `event_logs` がなければカテゴリ開始値へ戻す。
- 日付判定には Python の `datetime.now().date()` と SQLite の `DATE(..., 'localtime')` が使われている。

#### 既存文書のどの章に入れると自然か

`docs/REQUIREMENTS.md` の「FR-001: 番号発券機能」または「NFR-002: 可用性」に入れると自然である。

#### メンテナーに確認したいこと

- 「毎日0時に自動リセット」は厳密な時刻実行を意味するのか、翌営業日の初回発券時にリセットされればよいのか。
- サーバーのローカルタイムゾーンは必ず JST として運用するのか。
- 開庁時間外の発券や日跨ぎ発券を想定するか。

#### そのまま貼れる文章案

> 番号リセットは常駐バッチではなく、発券時に日付変更を検知して実行する方式とする。翌日最初の発券時に当日ログが存在しない場合、カテゴリごとの開始番号へ戻す。時刻基準はサーバーのローカル時刻を日本標準時として運用する前提とする。

### 4. 職員数の扱い

#### なぜあるとよいか

発券画面には対応職員数 1〜7 の選択があり、`event_logs` と `processing_logs` に保存される。一方、職員数が業務上どの指標に使われるかは docs 本文で強く説明されていない。将来の集計や分析に関係するなら REQUIREMENTS.md に前提を置くとよい。

#### コードから確認できた事実

- `templates/index.html` は 1〜7 の職員数ボタンを持つ。
- `static/script.js` は選択された職員数を `staffCount` として `/get_next_number` に送る。
- `/get_next_number` は `event_logs.staff_count` に保存する。
- `/start_processing` は対象の `event_logs.staff_count` を読み、`processing_logs.staff_count` に保存する。

#### 既存文書のどの章に入れると自然か

`docs/REQUIREMENTS.md` の「FR-005: データ記録・分析機能」に入れると自然である。

#### メンテナーに確認したいこと

- 職員数は待ち時間分析、窓口配置分析、当日状況メモのどれを目的にしているか。
- 未選択 `NULL` を許容する運用でよいか。
- 職員数 1〜7 は固定か、導入先で変更可能にする想定か。

#### そのまま貼れる文章案

> 発券時に任意で対応可能職員数を記録できる。職員数は発券ログに保存し、処理開始時には対応する処理ログにも引き継ぐ。未選択の場合は空値として扱う。

## メンテナーに確認したいこと

- API 仕様として、処理完了・不在戻しの識別子は `ticket_number` と `processing_id` のどちらを正にするか。
- 同一番号の `processing` レコードが複数存在する場合の正しい扱いは何か。
- `event_log_id` なしの旧形式データ互換をいつまで維持するか。
- カテゴリ A=1〜499、B=500〜799 は厳密な上限か、運用上の番号帯の目安か。
- 印刷失敗時の現場運用は、再発券、手書き、職員呼び出し、ログ確認のどれを標準とするか。
- 日次リセットは 0 時に即時実行される必要があるか、翌日初回発券時のリセットでよいか。
- サーバーのタイムゾーンは常に JST として固定運用するか。
- 職員数 1〜7 の記録は、どの分析・運用判断に使う想定か。
- CORS 許可 origin は本番でどの範囲にするか。
- 今後変更したいが、現時点では互換性のため残している仕様はどれか。
- コード上の実装と現場運用が異なる点はあるか。

## まだ既存docsへ直接反映しない理由

この文書は提案段階であり、既存 docs への完成版追記ではない。コードから確認できる事実を優先しているが、業務上の意図、現場運用、過去互換の維持方針はコードだけでは判断できない。

メンテナー確認前に `docs/ARCHITECTURE.md`、`docs/DEVELOPMENT.md`、`docs/REQUIREMENTS.md` へ直接統合すると、推測や誤読が本文に混ざる可能性がある。そのため、まず提案メモとして分離し、採用する項目、修正する項目、採用しない項目を判断できる状態に留める。

次の工程では、メンテナー追記、採否判断、レビュープロンプトを行い、コード・既存 docs・追記内容の整合性を確認したうえで必要な項目だけを既存 docs へ統合する。

## 次の工程

1. メンテナーが追記候補を確認する。
2. 採用する項目、修正する項目、採用しない項目を分ける。
3. メンテナーが業務上の意図や現場運用を追記する。
4. レビュープロンプトで、コード・既存 docs・追記内容の整合性を確認する。
5. 必要な項目だけを `docs/ARCHITECTURE.md`、`docs/DEVELOPMENT.md`、`docs/REQUIREMENTS.md` へ統合する。
