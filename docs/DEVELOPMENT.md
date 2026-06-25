# MADO queue — Development & Testing

> ローカルでビルド・起動・テストするための手順。実装の詳細は [ARCHITECTURE.md](ARCHITECTURE.md)、業務要件は [REQUIREMENTS.md](REQUIREMENTS.md) を参照。

---

## 1. 前提

- **Docker**（Docker Desktop もしくは WSL/Linux 上のネイティブ Docker Engine）
- もしくは Python 3.14 + 依存パッケージ（Docker を使わない場合）

プリンターは**接続していなくてもテスト可能**。印刷は失敗するが例外を握りつぶす設計のため、発券・採番・DB記録は成功する（ログに `[print_ticket] error: ...` が出るのは想定内）。

---

## 2. Docker で起動（推奨）

```bash
docker compose up          # フォアグラウンド起動（ログが流れる）
```

起動後、ブラウザで **http://localhost:8000** を開く。

> **WSL（Windows）の場合:** 必ず上記のように `-d` を付けずフォアグラウンドで起動し、ターミナルを開いたままにすること。`localhost` で繋がらない場合は本書末尾の **「7. WSL（Windows）でハマりやすい点」** を参照。

- 初回起動時に `entrypoint.sh` が DB を自動初期化し、`data/numbers.db` を生成する
- 止めるときは起動中のターミナルで **Ctrl+C**
- コード変更を反映して再ビルド：`docker compose up --build`

### 画面

| URL | 画面 | 利用者 |
|-----|------|--------|
| http://localhost:8000/ | 発券画面 | 来庁者（タブレット） |
| http://localhost:8000/processing | 処理管理画面 | 窓口職員（PC） |
| http://localhost:8000/display | 公開表示画面 | 待合エリア（大型モニター） |

### 動作確認（HTTP）

```bash
# トップページ
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/      # → 200

# 番号を発券
curl -s -X POST http://localhost:8000/get_next_number \
  -H "Content-Type: application/json" \
  -d '{"category":"A","buttonText":"住民票","timestamp":"2026-06-11T09:00:00+09:00"}'
# → {"category":"A","next_number":1}

# 表示画面用データ
curl -s http://localhost:8000/display_data
# → {"calling":[...],"waiting_count":N}
```

---

## 3. ローカルで起動（Docker を使わない場合）

```bash
pip install -r requirements.txt
python init_db.py                                   # 初回のみ（DB初期化）
python app.py                                       # 開発サーバー
waitress-serve --host=0.0.0.0 --port=8000 app:app   # 本番相当（Waitress）
```

> Windows でレシートプリンターを使う場合は `pip install pywin32` も必要（`requirements.txt` には含まない）。

---

## 4. テスト

```bash
python -m unittest test_app -v
```

テストは `print_ticket` をスタブ化しているため、プリンター・印刷の有無に依存しない。

---

## 5. DB のリセット

`data/numbers.db` をまっさらに戻したいとき：

```bash
docker compose down
rm data/numbers.db        # Windows の場合は data\numbers.db を削除
docker compose up         # 次回起動時に再初期化される
```

`data/` はホスト側にマウントされ永続化されるので、バックアップはこのファイルをコピーするだけ。

---

## 6. プリンター設定（任意）

USB 接続の ESC/POS レシートプリンターを使う場合、機種に応じて環境変数で指定する。

| 環境変数 | 既定値 | 説明 |
|---------|-------|------|
| `PRINTER_NAME` | `POS-80C (copy 1)` | Windows で使うプリンター名 |
| `PRINTER_VID` | `0x04b8` | USBベンダーID（Linux/pyusb で使用） |
| `PRINTER_PID` | `0x0e20` | USBプロダクトID（Linux/pyusb で使用） |

Docker（Linux）で実機プリンターに印刷するには、`docker-compose.yml` の `devices: /dev/bus/usb:/dev/bus/usb` のコメントを外す。WSL の場合は別途 `usbipd-win` で USB を WSL にアタッチする必要がある（UI・採番のテストだけなら不要）。

---

## 7. WSL（Windows）でハマりやすい点

Windows 上で **WSL 内のネイティブ Docker**（Docker Desktop ではない構成）を使う場合の注意。

### 7.1 `-d`（デタッチ）で起動すると、放置でコンテナごと止まる

WSL ディストロは、開いているセッションやプロセスが無くなるとアイドルで自動停止する。`docker compose up -d` はコマンドが即終了してセッションが閉じるため、しばらくするとディストロごと落ち、ブラウザから `ERR_CONNECTION_TIMED_OUT` になる。

**対策:** テスト中は `-d` を付けず、**フォアグラウンドで `docker compose up` を実行し、そのターミナルを開いたままにする**。

### 7.2 `localhost:8000` に繋がらないとき

ディストロが生きていれば WSL2 のポート転送が効き、Windows のブラウザから `localhost:8000` で到達できる。繋がらない場合は：

1. まず 7.1 のとおりフォアグラウンド起動でディストロを生かす
2. それでもダメなら WSL の IP で直接開く：
   ```bash
   wsl hostname -I        # 先頭のIP。例: 172.27.70.54 → http://172.27.70.54:8000
   ```
   ※ WSL の IP は再起動で変わる
3. 恒久的に `localhost` を使いたいなら **Docker Desktop（WSL2インテグレーション有効）** に切り替えるのが最も確実（公開ポートが自動で Windows の localhost に転送される）

> Windows 11 なら `.wslconfig` の `networkingMode=mirrored` で `localhost` を完全に共有できるが、**Windows 10 では非対応**。

### 7.3 改行コード（CRLF）

`entrypoint.sh` などのシェルスクリプトが CRLF 改行だと、コンテナ起動時に `not found` 等で失敗する。**LF を維持**すること（リポジトリの `.gitattributes` / エディタ設定で `*.sh` を LF に固定するのが安全）。

---

## 8. 通常運用手順

この節は、既存の開発手順と重複する `docs/OPERATION.md` を新設しないため、運用時によく使う手順を本ファイルへ統合したものです。

### 8.1 初回セットアップ

1. Docker を使う場合は `docker compose up --build` を実行する。
2. ローカル Python で起動する場合は `pip install -r requirements.txt` の後、初回のみ `python init_db.py` を実行する。
3. ブラウザで `http://localhost:8000/`、`http://localhost:8000/processing`、`http://localhost:8000/display` を開き、画面が表示されることを確認する。
4. プリンターを使う場合は、環境変数と USB 接続方式が実行環境に合っていることを確認する。

### 8.2 通常運用

1. サーバーまたは Docker コンテナを起動する。
2. 発券用タブレットで `/` を開く。
3. 職員 PC で `/processing` を開く。
4. 待合表示用 PC で `/display` を開く。
5. 業務終了後は、必要に応じて `data/numbers.db` をコピーしてバックアップする。

### 8.3 よく使うコマンド

| 目的 | コマンド |
|---|---|
| Docker 起動 | `docker compose up` |
| Docker 再ビルド起動 | `docker compose up --build` |
| Docker 停止 | `docker compose down` |
| ローカル DB 初期化 | `python init_db.py` |
| ローカル開発サーバー | `python app.py` |
| 本番相当起動 | `waitress-serve --host=0.0.0.0 --port=8000 app:app` |
| 既存テスト | `python -m unittest test_app -v` |
| 差分の空白チェック | `git diff --check` |

### 8.4 ログ・出力・成果物の確認方法

- アプリケーションログは、ローカル起動時はターミナル、Docker 起動時は `docker compose up` の標準出力で確認する。
- 印刷失敗は `[print_ticket] error: ...` として出力される。
- SQLite DB は `data/numbers.db` に保存される。テストや監査では実運用 DB を使わず、一時 DB またはテスト用 DB を使う。
- 発券履歴は `event_logs`、処理履歴は `processing_logs`、カテゴリ別カウンターは `numbers` に保存される。

### 8.5 トラブルシュート

| 症状 | 確認すること |
|---|---|
| 画面が開かない | サーバーが起動しているか、ポート `8000` が使えるか、WSL の場合は本書 7 章の注意点に該当しないか確認する。 |
| 番号は出るが印刷されない | プリンター接続、環境変数、Docker の USB デバイス設定、Windows のプリンター名を確認する。 |
| DB が初期化されない | `data/numbers.db` の有無、`entrypoint.sh` の実行権限、`init_db.py` の実行結果を確認する。 |
| テストで実 DB を触りそう | テスト用 DB へ差し替えられているか、`print_ticket` がスタブ化されているか確認する。 |
| 画面の CSS/JS が期待通りでない | CDN 参照がネットワーク的に利用できるか、ブラウザの開発者ツールで読み込み失敗を確認する。 |

### 8.6 変更時に確認すべき点

- API のリクエスト・レスポンスを変える場合は、`docs/ARCHITECTURE.md` と既存テストを同時に確認する。
- カテゴリ、番号帯、印字内容を変える場合は、`docs/REQUIREMENTS.md` の業務要件と窓口運用への影響を確認する。
- DB スキーマを変える場合は、新規 DB 用の `init_db.py` と既存 DB 用の `safe_migrate_db.py` の両方を確認する。
- プリンター処理を変える場合は、プリンター未接続環境でも発券・DB 記録が検証できるようにスタブ化する。
- ドキュメントを増やす場合は、既存文書へ統合できないかを先に確認し、大小文字違い・類似名ファイルを作らない。
