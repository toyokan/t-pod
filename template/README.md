# イベント情報入力シート → JSON 生成フロー

新規イベントページ（`events/<id>.json`）を、JSON を書かずに作るためのひな形です。
担当者が **Excel に記入** → **Claude Code が JSON を生成** → ページ公開、という流れを想定しています。

## ファイル
| ファイル | 役割 |
| --- | --- |
| `イベント情報入力シート.xlsx` | 担当者が記入する Excel ひな形（記入例つき） |
| `make_template.py` | 上記 Excel を再生成するスクリプト（`pip install openpyxl` 後 `python3 template/make_template.py`） |

## 使い方（担当者むけ）
1. `イベント情報入力シート.xlsx` を開く。各シートに **記入例が入っている** ので、それを上書き／参考にして入力する。
2. 入力できたら、この Excel ファイルを Claude Code のセッションに渡し、こう依頼する:

   > このExcelから `events/<id>.json` を生成し、`events.json` に一覧エントリを追記してください。

3. Claude が JSON を生成・追記したら、開発者が確認してデプロイ（`main` にマージ）。

## 各シートの記入ルール
| シート | 入る場所(JSON) | 記入のポイント |
| --- | --- | --- |
| **基本情報** | `eventInfo` ＋ `events.json` | 縦並び。研究会名・テーマ・会場・ブランド色(16進)・イベントID(半角英数/ハイフン/アンダースコア)・並び順日付(YYYY-MM-DD)。下部に「開催日ごと(dates)」「会場一覧(rooms)」の小表。 |
| **タイムテーブル** | `sessions` | 1行=1アイテム。`日付ID` は基本情報の開催日に対応(day1/day2…)。会場別の並行セッションは **会場名を入れて行を分ける**。`登壇者など(meta)` は **セル内改行(Alt+Enter)で1行=1要素**。受付・昼食など演題なしは title/meta 空欄。 |
| **資料リンク** | `venue.resourceLinks` ／ `forms` | `種別` で振り分け: 「資料」「ホームページ」→ 資料リンク、「事後アンケート」「参加申し込み」「次回案内希望」→ フォーム。 |
| **関連書籍** | `books` | 書名・著者・出版社・表紙URL・紹介文・商品URL・Amazon URL。 |
| **概要・お知らせ** | `eventInfo.notices` | `重要度(level)` は `important`(強調) か `info`(通常)。 |

## 変換仕様（Claude むけ）
Excel から JSON を生成するときの規則。**構造の正は既存の `events/2026-zensanken-37.json`** とする。

- **基本情報** → `eventInfo` の `title`/`subtitle`/`tagline`/`logoMain`/`logoSub`/`theme`/`venueName`/`dateRange`/`brandColor`、`venue.mapNote`。`dates[]`（`id` は day1/day2… を自動採番、`label`/`date`/`weekday`/`time`）、`rooms[]`（`id`=`name`=会場名、`color`）。`events.json` には `id`/`title`/`theme`/`dateRange`/`venueName`/`sortDate`(=並び順日付) を1エントリ追記。
  - PWA アイコン文字はデフォルトで `logoMain` 先頭3文字。**ヘッダー表示（`logoMain`）とアイコン文字を別にしたい場合**（例: ヘッダー「算数サマー2026」・アイコン「算サマ」）は `eventInfo.iconLabel` を追加で指定する（任意、Excel シートに列は無いため依頼文で指示）。
- **タイムテーブル** → `sessions[]`。同じ `日付ID`+`開始`+`終了`+`区分`+(会場以外)の並行行は1セッションに束ね、各行を `items[]` の要素にする。`title` と `meta`（セル内改行を `\n` で分割し配列化）を格納。会場列があれば `item.room`。`note` 列はセッションの `note`。演題・登壇者が無い区分（受付/昼食など）は `items: []`。各セッションに `id`（例 d1-01）を採番。
- **資料リンク** → `種別` で `eventInfo.venue.resourceLinks[]`（資料/ホームページ）と `eventInfo.forms[]`（アンケート/申し込み/案内希望）に振り分け。各要素は `label`/`description`/`url`。
- **関連書籍** → `books[]`（`title`/`author`/`publisher`/`cover`/`description`/`url`/`amazon_url`）。
- **概要・お知らせ** → `eventInfo.notices[]`（`title`/`body`/`level`）。

### 仕上げ
- 生成後に妥当性チェック: `python3 -m json.tool events/<id>.json`。
- **会場マップ（イベント別）**: 会場はイベント毎に異なる。会場図があれば `assets/venue-map-<id>.svg`（または `.png`/`.jpg`）として置き `eventInfo.venue.mapImage` に相対パス指定、または外部公開URL（Google Drive 等）を指定。無ければ `mapImage` を省略し `mapNote` のみで運用（画像は非表示になる）。
- PWA アプリ名を安定させるため、必要なら `events/<id>.webmanifest` を作成し、`eventInfo.manifestPath` に指定（既存イベント参照）。
- 注意（CLAUDE.md より）: **過去の `events/<id>.json` は削除しない**。`index.html` に固有文言を書かない。配布資料の実ファイルは置かず外部リンクを記載。
