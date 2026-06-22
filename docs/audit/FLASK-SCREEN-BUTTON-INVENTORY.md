# MADO-queue Flask Screen & Button Inventory

## 1. Purpose

この文書は、MADO-queue のFlask実装から確認できる画面、ボタン、操作、JavaScript処理、API呼び出しを棚卸しする外部監査メモです。

Scope reviewed:

- `app.py`
- `templates/*.html`
- `static/*.js`
- `static/*.css`
- `docs/REQUIREMENTS.md`
- `docs/ARCHITECTURE.md`

Notes on evidence:

- **Fact:** code or documentation directly states the item.
- **Inference:** implementation behavior is inferred from code paths, SQL filters, DOM updates, or JavaScript control flow.
- This document does not evaluate UX quality and does not propose production behavior changes.

## 2. Routes and Screens

| Route | Method | Template | Purpose from code/docs | Main user if documented |
|---|---|---|---|---|
| `/` | GET | `templates/index.html` | 発券画面。手続き種別と任意の対応職員数を選び、`/get_next_number` で番号を発行する。 | 来庁者（市民） / タブレット端末 |
| `/processing` | GET | `templates/syori.html` | 職員処理管理画面。本日の呼び出し待ちと対応中を表示し、呼び出し・削除・不在戻し・完了を操作する。 | 窓口職員 / PCブラウザ |
| `/display` | GET | `templates/display.html` | 公開表示画面。呼び出し中番号と待ち人数を `/display_data` から取得して表示する。 | 待合室の来庁者 / 大型ディスプレイ |
| `/get_next_number` | POST | None; JSON API | 番号発行API。`numbers` を更新し、`event_logs` に発行ログを挿入し、カテゴリD以外は印刷処理を呼ぶ。 | UI caller: `/` |
| `/start_processing` | POST | None; JSON API | 呼び出し開始API。`processing_logs` に `status='processing'` のレコードを挿入する。 | UI caller: `/processing` |
| `/end_processing` | POST | None; JSON API | 処理終了API。本日の `processing` レコードを `completed` に更新する。 | UI caller: `/processing` |
| `/cancel_processing` | POST | None; JSON API | 不在戻しAPI。本日の `processing` レコードを削除し、待ち一覧に復帰しうる状態にする。 | UI caller: `/processing` |
| `/delete_ticket` | POST | None; JSON API | 削除API。`processing_logs` に `status='deleted'` のレコードを挿入する。 | UI caller: `/processing` |
| `/display_data` | GET | None; JSON API | 公開表示画面向けデータAPI。対応中リストと待ち人数を返す。 | UI caller: `/display` |

## 3. Screen Inventory

### `/`

- template: `templates/index.html`
- static files used:
  - `static/lib/bootstrap.min.css`
  - `static/style.css`
  - `static/script.js`
- displayed buttons:
  - 対応職員数 buttons: `1`, `2`, `3`, `4`, `5`, `6`, `7`
  - Category A buttons:
    - `住民票`
    - `戸籍謄本（抄本）`
    - `印鑑証明`
    - `らくらく証明`
    - `現況届`
  - Category B buttons:
    - `広域交付・戸籍収集（出生～死亡）`
    - `印鑑登録・変更`
    - `転出`
    - `転居`
    - `世帯異動（主変、合併・分離）`
    - `マイカ受取`
    - `マイカ更新`
    - `マイカ暗証番号`
    - `マイカ申請・紛失`
    - `転入`
  - Category C buttons:
    - `戸籍届出`
    - `年金`
    - `おくやみ`
    - `パスポート申請`
    - `パスポート受取（紙・OL）`
    - `火葬許可`
    - `その他`
  - Category D button:
    - `窓口以外の来庁者`
- button labels:
  - The visible Category B button `広域交付・戸籍収集（出生～死亡）` sends `buttonText: '戸籍収集（出生～死亡）'` to JavaScript/API. Fact: visible label and API text differ.
  - The visible Category C button `火葬許可` sends `buttonText: '火葬許可証'` to JavaScript/API. Fact: visible label and API text differ.
- form/input elements:
  - No `<form>` element is used.
  - Staff count is held in JavaScript variable `selectedStaffCount`; the page does not use a hidden input.
  - Category is supplied through `data-category` attributes on ticket buttons.
- JavaScript event handlers:
  - Inline `onclick="selectStaff(n)"` on staff count buttons.
  - Inline `onclick="issueTicket(this, '<buttonText>')"` on ticket buttons.
  - `issueTicket()` optionally calls `navigator.vibrate(100)` when supported.
  - `issueTicket()` adds `active` class to the clicked button and removes it after 500 ms.
- API calls:
  - `POST /get_next_number`
  - Payload: `{ category, buttonText, timestamp, staffCount }`
  - `timestamp` is generated in the browser using `Intl.DateTimeFormat` with `timeZone: 'Asia/Tokyo'`, then converted to a string intended to include `+09:00`.
- resulting DB/log effect if traceable:
  - `numbers.current_number` and `numbers.timestamp` are updated for the submitted category.
  - `event_logs` receives `{ category, button_text, timestamp, current_number, staff_count }`.
  - Category D returns without printing in `print_ticket()`.
  - Categories other than D call `print_ticket()` after DB commit; print errors are caught and logged but do not change the returned success JSON.
- related CSS classes:
  - Bootstrap classes: `container`, `p-5`, `mb-4`, `p-3`, `border`, `rounded`, `bg-light`, `d-flex`, `align-items-center`, `flex-wrap`, `font-weight-bold`, `mr-3`, `btn-group`, `btn`, `btn-outline-dark`, `btn-dark`, `btn-primary`, `btn-secondary`, `btn-success`, `btn-block`, `mb-2`, `mt-2`, `text-center`, `table`, `table-bordered`, `ml-3`, `text-muted`.
  - App stylesheet classes/rules: `.btn-block`, `.btn-custom:active`, media queries for `.container` and `.btn-block`.
- notes: fact only / inferred:
  - Fact: `/` is documented as the 発券画面 and intended for 来庁者/タブレット.
  - Fact: staff count selection is optional in the JavaScript and API payload can send `null`.
  - Fact: the UI does not disable ticket buttons during the `/get_next_number` request.
  - Inference: rapid repeated taps can send multiple POST requests because `issueTicket()` has no in-flight guard or button disabling.

### `/processing`

- template: `templates/syori.html`
- static files used:
  - `static/lib/bootstrap.min.css`
  - Inline `<style>` and inline `<script>` in the template.
- displayed buttons:
  - In waiting-list cards:
    - `呼び出し (処理開始)`
    - `削除`
  - In processing-list cards:
    - `不在 (待ちに戻す)`
    - `完了 (処理終了)`
- button labels:
  - Waiting heading: `呼び出し待ち (Waiting)`.
  - Processing heading: `対応中 (Processing)`.
  - Empty states: `待ち人数はいません`, `対応中のお客様はいません`.
- form/input elements:
  - No `<form>` element is used.
  - Button `data-*` attributes carry record values from Jinja:
    - waiting: `data-number`, `data-category`, `data-button-text`, `data-timestamp`, `data-event-log-id`
    - processing: `data-number`
- JavaScript event handlers:
  - `DOMContentLoaded` initializes event listeners and auto reload.
  - `.startProcessing` click:
    - records user interaction
    - sets `isProcessing = true`
    - disables the clicked button
    - sends `POST /start_processing`
    - reloads on success; alerts and re-enables on API or network failure
    - the confirm dialog is present only as commented code and is not executed
  - `.endProcessing` click:
    - asks `confirm('処理を完了してもよろしいですか？')`
    - disables the clicked button after confirmation
    - sends `POST /end_processing`
    - reloads on success; alerts and re-enables on API or network failure
  - `.cancelProcessing` click:
    - asks `confirm('この番号を待ち行列に戻しますか？')`
    - disables the clicked button after confirmation
    - sends `POST /cancel_processing`
    - reloads on success; alerts and re-enables on API or network failure
  - `.deleteTicket` click:
    - asks `confirm('この番号を削除してもよろしいですか？')`
    - disables the clicked button after confirmation
    - sends `POST /delete_ticket`
    - reloads on success; alerts and re-enables on API or network failure
  - Auto reload interval:
    - every 10 seconds
    - reloads only when `!isProcessing` and at least 5 seconds have passed since last recorded interaction
- API calls:
  - `POST /start_processing`
  - `POST /end_processing`
  - `POST /cancel_processing`
  - `POST /delete_ticket`
- resulting DB/log effect if traceable:
  - `POST /start_processing`: inserts `processing_logs` row with `status='processing'`, `start_time`, `wait_time`, `created_at`, `staff_count`, and optional `event_log_id`.
  - `POST /end_processing`: updates matching same-day `processing_logs` row(s) for `ticket_number` and `status='processing'` to `status='completed'`, with `end_time` and `processing_time`.
  - `POST /cancel_processing`: deletes matching same-day `processing_logs` row(s) for `ticket_number` and `status='processing'`.
  - `POST /delete_ticket`: inserts `processing_logs` row with `status='deleted'`, `wait_time=0`, and optional `event_log_id`.
  - Waiting list excludes Category D and excludes event logs that have a same-day processing/deleted/completed processing log by `event_log_id` or legacy `ticket_number + category` match.
- related CSS classes:
  - Inline custom classes: `.waiting-col`, `.processing-col`, `.card-number`, `.card-time`.
  - Bootstrap classes: `container-fluid`, `row`, `col-md-6`, `p-4`, `text-center`, `mb-4`, `text-primary`, `list-group`, `list-group-item`, `list-group-item-action`, `flex-column`, `align-items-start`, `mb-3`, `shadow-sm`, `d-flex`, `w-100`, `justify-content-between`, `mb-1`, `text-muted`, `btn`, `btn-primary`, `btn-danger`, `btn-sm`, `btn-block`, `mt-1`, `mt-2`, `btn-warning`, `btn-success`, `border-primary`, `alert`, `alert-info`, `alert-light`.
- notes: fact only / inferred:
  - Fact: `/processing` renders waiting and processing lists server-side before sending HTML.
  - Fact: the processing-side buttons identify records only by `ticket_number` in the UI payload.
  - Fact: `isProcessing` is set to `true` before fetches and reset only on failure/cancel confirmation branches; successful branches reload the page.
  - Inference: a successful operation depends on page reload to reset client-side `isProcessing`.

### `/display`

- template: `templates/display.html`
- static files used:
  - No external CSS/JS files; CSS and JavaScript are inline.
- displayed buttons / clickable UI:
  - No `<button>` elements are used.
  - `#audioNotice` is a clickable `<div>` with inline `onclick="unlockAudio()"`.
  - UI text: `🔊 呼び出し音を有効にするには、この画面をクリックしてください`.
- button labels:
  - Not applicable for `<button>` labels.
  - Clickable audio banner text is listed above.
- form/input elements:
  - No `<form>` or input elements are used.
- JavaScript event handlers:
  - `onclick="unlockAudio()"` on `#audioNotice`.
  - `setInterval(updateClock, 1000)` updates `#clock`.
  - `updateDisplay()` is called once on load and then every 3000 ms.
  - `updateDisplay()` fetches `/display_data`, filters calling records to `seconds_since < 60`, limits them to 5, detects new calling keys, optionally plays a Web Audio chime, updates `#callingCards`, and writes `waiting_count` to `#waitingCount`.
- API calls:
  - `GET /display_data`
- resulting DB/log effect if traceable:
  - No write effect from `/display` or its JavaScript.
  - `/display_data` reads `processing_logs` and `event_logs` through `_WAITING_LIST_SQL`.
- related CSS classes:
  - Inline custom classes: `.calling-section`, `.calling-header`, `.calling-body`, `.card`, `.card-category`, `.card-number`, `.card-label`, `.card-calling`, `.no-card`, `.waiting-bar`, `.waiting-bar-label`, `.waiting-bar-count`, `.waiting-bar-unit`.
  - CSS animation: `@keyframes blink`; `.card-calling` uses `animation: blink 1s ease-in-out infinite`.
- notes: fact only / inferred:
  - Fact: display page initially shows `現在呼び出し中の番号はありません` until JavaScript replaces the content.
  - Fact: category names are mapped for A/B/C only; any other category is displayed as raw category value after escaping.
  - Fact: a new calling set does not play the chime on the first `updateDisplay()` because `prevCallingKeys.size > 0` is required.
  - Inference: the first visible state after load can update without chime even if there are currently processing tickets.

## 4. Button Inventory

| Screen | Button label / UI text | HTML element | JS handler | API endpoint | HTTP method | Expected effect | Log/DB effect | Source file |
|---|---|---|---|---|---|---|---|---|
| `/` | `1` through `7` | `<button type="button" class="btn btn-outline-dark staff-btn">` | `selectStaff(count)` inline `onclick` | None | None | Selects staff count and updates staff display text. | No DB effect until a ticket is issued; selected value is later sent as `staffCount`. | `templates/index.html`, `static/script.js` |
| `/` | `住民票` | `<button data-category="A">` | `issueTicket(this, '住民票')` | `/get_next_number` | POST | Issues Category A ticket and updates `#numberA`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `戸籍謄本（抄本）` | `<button data-category="A">` | `issueTicket(this, '戸籍謄本（抄本）')` | `/get_next_number` | POST | Issues Category A ticket and updates `#numberA`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `印鑑証明` | `<button data-category="A">` | `issueTicket(this, '印鑑証明')` | `/get_next_number` | POST | Issues Category A ticket and updates `#numberA`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `らくらく証明` | `<button data-category="A">` | `issueTicket(this, 'らくらく証明')` | `/get_next_number` | POST | Issues Category A ticket and updates `#numberA`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `現況届` | `<button data-category="A">` | `issueTicket(this, '現況届')` | `/get_next_number` | POST | Issues Category A ticket and updates `#numberA`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `広域交付・戸籍収集（出生～死亡）` | `<button data-category="B">` | `issueTicket(this, '戸籍収集（出生～死亡）')` | `/get_next_number` | POST | Issues Category B ticket and updates `#numberB`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `印鑑登録・変更` | `<button data-category="B">` | `issueTicket(this, '印鑑登録・変更')` | `/get_next_number` | POST | Issues Category B ticket and updates `#numberB`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `転出` | `<button data-category="B">` | `issueTicket(this, '転出')` | `/get_next_number` | POST | Issues Category B ticket and updates `#numberB`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `転居` | `<button data-category="B">` | `issueTicket(this, '転居')` | `/get_next_number` | POST | Issues Category B ticket and updates `#numberB`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `世帯異動（主変、合併・分離）` | `<button data-category="B">` | `issueTicket(this, '世帯異動')` | `/get_next_number` | POST | Issues Category B ticket and updates `#numberB`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `マイカ受取` | `<button data-category="B">` | `issueTicket(this, 'マイカ受取')` | `/get_next_number` | POST | Issues Category B ticket and updates `#numberB`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `マイカ更新` | `<button data-category="B">` | `issueTicket(this, 'マイカ更新')` | `/get_next_number` | POST | Issues Category B ticket and updates `#numberB`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `マイカ暗証番号` | `<button data-category="B">` | `issueTicket(this, 'マイカ暗証番号')` | `/get_next_number` | POST | Issues Category B ticket and updates `#numberB`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `マイカ申請・紛失` | `<button data-category="B">` | `issueTicket(this, 'マイカ申請・紛失')` | `/get_next_number` | POST | Issues Category B ticket and updates `#numberB`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `転入` | `<button data-category="B">` | `issueTicket(this, '転入')` | `/get_next_number` | POST | Issues Category B ticket and updates `#numberB`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `戸籍届出` | `<button data-category="C">` | `issueTicket(this, '戸籍届出')` | `/get_next_number` | POST | Issues Category C ticket and updates `#numberC`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `年金` | `<button data-category="C">` | `issueTicket(this, '年金')` | `/get_next_number` | POST | Issues Category C ticket and updates `#numberC`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `おくやみ` | `<button data-category="C">` | `issueTicket(this, 'おくやみ')` | `/get_next_number` | POST | Issues Category C ticket and updates `#numberC`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `パスポート申請` | `<button data-category="C">` | `issueTicket(this, 'パスポート申請')` | `/get_next_number` | POST | Issues Category C ticket and updates `#numberC`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `パスポート受取（紙・OL）` | `<button data-category="C">` | `issueTicket(this, 'パスポート受取（紙・OL）')` | `/get_next_number` | POST | Issues Category C ticket and updates `#numberC`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `火葬許可` | `<button data-category="C">` | `issueTicket(this, '火葬許可証')` | `/get_next_number` | POST | Issues Category C ticket and updates `#numberC`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `その他` | `<button data-category="C">` | `issueTicket(this, 'その他')` | `/get_next_number` | POST | Issues Category C ticket and updates `#numberC`. | Updates `numbers`; inserts `event_logs`; calls print for non-D. | `templates/index.html`, `static/script.js`, `app.py` |
| `/` | `窓口以外の来庁者` | `<button data-category="D">` | `issueTicket(this, '窓口以外の来庁者')` | `/get_next_number` | POST | Issues Category D ticket and updates `#numberD`. | Updates `numbers`; inserts `event_logs`; print skipped by `print_ticket()`. | `templates/index.html`, `static/script.js`, `app.py` |
| `/processing` | `呼び出し (処理開始)` | `<button class="startProcessing">` | `.startProcessing` click listener | `/start_processing` | POST | Moves visible ticket from waiting to processing after successful reload. | Inserts `processing_logs.status='processing'`. | `templates/syori.html`, `app.py` |
| `/processing` | `削除` | `<button class="deleteTicket">` | `.deleteTicket` click listener with confirm | `/delete_ticket` | POST | Removes visible ticket from waiting after successful reload. | Inserts `processing_logs.status='deleted'`. | `templates/syori.html`, `app.py` |
| `/processing` | `不在 (待ちに戻す)` | `<button class="cancelProcessing">` | `.cancelProcessing` click listener with confirm | `/cancel_processing` | POST | Returns processing ticket to waiting after successful reload. | Deletes same-day `processing_logs.status='processing'` row(s) matching ticket number. | `templates/syori.html`, `app.py` |
| `/processing` | `完了 (処理終了)` | `<button class="endProcessing">` | `.endProcessing` click listener with confirm | `/end_processing` | POST | Completes processing ticket after successful reload. | Updates same-day `processing_logs.status='processing'` row(s) matching ticket number to `completed`. | `templates/syori.html`, `app.py` |
| `/display` | `🔊 呼び出し音を有効にするには、この画面をクリックしてください` | `<div id="audioNotice">` | `unlockAudio()` inline `onclick` | None | None | Enables/resumes Web Audio context, hides banner, calls `playChime()`. | No DB effect. | `templates/display.html` |

## 5. API Calls from UI

| Caller screen | API endpoint | Method | Payload | Response use | Related function in app.py |
|---|---|---|---|---|---|
| `/` | `/get_next_number` | POST | `{ category, buttonText, timestamp, staffCount }` | If `data.error`, show `alert`. Otherwise set `#number${category}` to `次の番号: ${data.next_number}`. | `get_next_number()` |
| `/processing` | `/start_processing` | POST | `{ ticket_number, category, button_text, timestamp, event_log_id }` | If `data.success`, reload page. Otherwise show `alert`, re-enable button, reset `isProcessing`. | `start_processing()` |
| `/processing` | `/end_processing` | POST | `{ ticket_number }` | If `data.success`, reload page. Otherwise show `alert`, re-enable button, reset `isProcessing`. | `end_processing()` |
| `/processing` | `/cancel_processing` | POST | `{ ticket_number }` | If `data.success`, reload page. Otherwise show `alert`, re-enable button, reset `isProcessing`. | `cancel_processing()` |
| `/processing` | `/delete_ticket` | POST | `{ ticket_number, category, button_text, event_log_id }` | If `data.success`, reload page. Otherwise show `alert`, re-enable button, reset `isProcessing`. | `delete_ticket()` |
| `/display` | `/display_data` | GET | None | Filters `calling` to records with `seconds_since < 60`, slices to max 5, updates calling cards and waiting count, may play chime for newly detected calling keys. | `display_data()` |

## 6. State Transitions

Code-visible statuses and display states:

- `issued`
  - Inference: there is no literal `issued` status in the database. A ticket is effectively issued when a row exists in `event_logs` after `/get_next_number`.
  - DB fact: `/get_next_number` inserts into `event_logs` and updates `numbers`.
- `waiting`
  - Inference: there is no literal `waiting` status in the database. The waiting list is derived from `event_logs` rows for today, excluding Category D, for which no same-day matching `processing_logs` row exists.
- `processing`
  - Fact: `/start_processing` inserts a `processing_logs` row with `status='processing'`.
  - Fact: `/processing` reads same-day `processing_logs.status='processing'` rows for the right-side processing list.
  - Fact: `/display_data` reads same-day `processing_logs.status='processing'` rows for public display data.
- `completed`
  - Fact: `/end_processing` updates same-day `processing_logs` rows matching `ticket_number` and `status='processing'` to `status='completed'` and sets `end_time` and `processing_time`.
- `deleted`
  - Fact: `/delete_ticket` inserts a `processing_logs` row with `status='deleted'`.
  - Inference: because the waiting-list SQL excludes event logs with any same-day matching processing log row, a deleted ticket no longer appears in the waiting list.
- `cancelled` / returned to waiting
  - Inference: there is no literal `cancelled` status. `/cancel_processing` deletes the same-day matching `processing` row, allowing the original `event_logs` row to match the derived waiting-list conditions again.

Observed transition paths from UI:

1. `/` ticket button → `POST /get_next_number` → `event_logs` row exists → **Inference: issued / waiting** for categories A-C.
2. `/processing` `呼び出し (処理開始)` → `POST /start_processing` → `processing_logs.status='processing'` → **processing**.
3. `/processing` `完了 (処理終了)` → `POST /end_processing` → `processing_logs.status='completed'` → **completed**.
4. `/processing` `不在 (待ちに戻す)` → `POST /cancel_processing` → processing log row deleted → **Inference: waiting again**.
5. `/processing` `削除` → `POST /delete_ticket` → `processing_logs.status='deleted'` → **deleted**.
6. `/` Category D button → `POST /get_next_number` → `event_logs` row exists, print skipped, and Category D excluded from waiting-list SQL → **Inference: issued but not managed in waiting/processing UI**.

## 7. UX-relevant Implementation Notes

Implementation facts that may affect UX, without evaluating whether they are good or bad:

- Auto update intervals:
  - `/display` calls `updateDisplay()` every 3000 ms.
  - `/display` updates the clock every 1000 ms.
  - `/processing` attempts auto reload every 10000 ms, but skips reload if `isProcessing` is true or if less than 5000 ms passed since last recorded interaction.
- Double-click / repeated-submit handling:
  - `/processing` disables the clicked action button before each fetch after confirmation, except when confirmation is cancelled.
  - `/` ticket buttons are not disabled during `/get_next_number`; only an `active` class is added temporarily.
- Confirmation dialogs:
  - `/processing` start processing has no active confirmation dialog; the confirm line is commented out.
  - `/processing` end processing asks `処理を完了してもよろしいですか？`.
  - `/processing` cancel processing asks `この番号を待ち行列に戻しますか？`.
  - `/processing` delete asks `この番号を削除してもよろしいですか？`.
- Error display:
  - `/` shows `alert('Error: ...')` when the API JSON contains `error`; network errors are logged to console only.
  - `/processing` shows alert dialogs for API errors and network errors.
  - `/display` logs fetch errors to console only.
- Print success/failure display:
  - `/` does not display explicit print success/failure state.
  - Server-side `print_ticket()` catches print exceptions and logs them, while `/get_next_number` still returns the issued number after DB commit.
- Audio chime:
  - `/display` uses Web Audio API generated tones.
  - Audio requires clicking the audio notice to set `audioUnlocked = true` and hide the notice.
  - New calls trigger chime only after at least one previous calling-key set exists.
- Public display filtering:
  - `/display_data` returns all same-day processing records, but `/display` displays only records with `seconds_since < 60` and only the first 5 after filtering.
- Text escaping:
  - `/display` escapes category and number before inserting card HTML with `innerHTML`.
- Mobile/tablet CSS:
  - `static/style.css` sets body font size, `.btn-block` font size to 24px, button spacing, and media query rules for tablet-width containers and portrait button padding.
- Category display:
  - `/display` maps only A/B/C to `カテゴリ A/B/C`; other categories fall back to their raw escaped category value.
- Documentation/code text differences visible in UI inventory:
  - Requirements list Category B `戸籍収集（出生〜死亡）`; the HTML visible button is `広域交付・戸籍収集（出生～死亡）`, while the sent `buttonText` is `戸籍収集（出生～死亡）`.
  - Requirements list Category C `火葬許可`; the HTML visible button is `火葬許可`, while the sent `buttonText` is `火葬許可証`.
  - Architecture documents `/end_processing` and `/cancel_processing` request examples using `processing_id`, but the current UI and Flask implementation use `ticket_number`.
  - Architecture states the `/start_processing` example includes `staff_count`, but the current UI sends no `staff_count`; the server derives `staff_count` from `event_logs` when possible.

## 8. Unknowns / Needs Manual Check

The following cannot be concluded from code alone:

- 実画面での視認性.
- タブレットでの押しやすさ.
- 待合室モニターでの可読性.
- 職員が状態を誤解しないか.
- 来庁者がボタン文言を理解できるか.
- 実端末ブラウザで音声有効化バナーが運用上クリックされるか.
- 実端末で `navigator.vibrate(100)` が期待どおり動作するか.
- プリンター故障時に来庁者または職員が画面表示から失敗を認識できるか.
- 32インチ以上の大型モニターで最大5件表示時の実際の収まり.
- PCブラウザで10秒自動更新が職員操作を妨げないか.
- URL分離のみの画面アクセスが現場運用に合っているか.
- Category D の「番号発行のみ（印刷なし）」という業務上の扱いが、待ち/処理画面に出ない実装で期待どおりか.
