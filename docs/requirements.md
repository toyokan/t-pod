# t-pod 要件・データ仕様

この文書は、公開トップページ向けの `README.md` から分離した実装・運用の詳細です。リポジトリが public の場合、この文書も公開されます。

## 1. 目的と構成

t-pod は教育イベント・研究会向けの静的タイムテーブル PWA である。ビルド工程は持たず、`index.html`、Vanilla JavaScript、Tailwind CSS Play CDN で動作する。

- `?id=<id>` あり: `events/<id>.json` を読み込むイベントモード
- `?id` なし: `events.json` を読み込む一覧モード
- イベント ID は `[A-Za-z0-9_-]` のみ許可する
- `index.html` は汎用シェルとし、個別イベント固有の文言を置かない
- 文字列を HTML に入れる場合は `escapeHtml()` を通す

## 2. ファイルの責務

| ファイル | 責務 | 通常のイベント追加時 |
| --- | --- | --- |
| `index.html` | 汎用 UI、描画、操作、PWA 実行時設定 | 変更しない |
| `events.json` | 一覧ページ用のイベント索引 | 1件追加 |
| `events/<id>.json` | イベントの全データ | 新規作成・編集 |
| `events/<id>.webmanifest` | イベント別 PWA マニフェスト | 任意（推奨） |
| `sw.js` | Network First キャッシュ、ナビゲーション HTML の `theme-color` 書換え | 通常は変更しない |
| `assets/` | アイコン、会場マップ等 | 任意 |
| `template/` | Excel 入力ひな形と生成スクリプト | 入力項目追加時に同期 |

`index.html` やアプリシェルを変更した場合は、`sw.js` の `CACHE_VERSION` を必ず上げる。

## 3. 主な機能要件

- TIMETABLE / FILES / BOOKS の3タブを表示する
- タブはボトムナビと左右スワイプで切り替える。スワイプ中は現在画面と移動先画面が指に追従する
- 開催日は当日を初期選択し、進行中または直近のセッションへ自動スクロールする
- 固定ヘッダーとボトムナビは半透明＋ぼかしを使い、非対応環境では不透明背景へフォールバックする
- タブ切替・押下・現在セッションの強調は、短時間の軽量な演出とし、`prefers-reduced-motion` では停止する
- お知らせは内容単位で既読を `localStorage` に保存し、未読件数を表示する
- LINE 友だち追加ポップアップはイベントでは `eventInfo.linePromo: true` の場合のみ表示する
- イベント別ブランド色、補助色、PWA 表示名、アイコン文字、会場マップを設定できる
- `eventInfo.bookSale` がある場合、BOOKS に特設販売ページへの導線を表示する
- `prefers-reduced-motion` と `backdrop-filter` 非対応環境にフォールバックする
- Service Worker は Network First とし、閲覧済みイベントをオフラインでも表示できるようにする

## 4. `events.json`

| キー | 内容 |
| --- | --- |
| `siteTitle` / `siteSubtitle` | 一覧ページのヘッダー文言 |
| `events[]` | 一覧表示するイベント |
| `events[].id` | `events/<id>.json` の `<id>` |
| `events[].title` / `theme` / `dateRange` / `venueName` | カード表示文言 |
| `events[].sortDate` | `YYYY-MM-DD`。新しい順の並び替えに使用 |
| `events[].brandColor` | 任意。イベントカードのアクセント色 |

`theme` と `brandColor` は原則として個別 JSON の値と揃える。

## 5. `events/<id>.json`

### `eventInfo`

| キー | 内容 |
| --- | --- |
| `title` / `subtitle` | 正式名称とフォールバック文言 |
| `logoMain` / `logoSub` | ヘッダーのロゴ表示。未指定時は `title` / `subtitle` を使用 |
| `appName` | 任意。ホーム画面用の短いアプリ名 |
| `iconLabel` | 任意。実行時生成アイコンの文字。未指定時は `logoMain` 先頭3文字 |
| `theme` | イベントテーマ。`――`、`―`、`—`、`〜` の最初の区切りでサブテーマを改行 |
| `venueName` / `dateRange` | 会場・会期の表示文言 |
| `organizer` / `coOrganizer` / `cooperation` / `support` | 任意。主催・共催・協力・後援。文字列または文字列配列 |
| `tagline` | 任意。短いキャッチ |
| `brandColor` | 主ブランド色（16進）。未指定時は既定色 |
| `brandColor2` | 任意。ヘッダー等のグラデーション補助色 |
| `linePromo` | 任意。`true` のイベントだけ LINE 導線を自動表示 |
| `manifestPath` | 任意。`events/<id>.webmanifest` 形式の実体マニフェストパス |
| `dates[]` | `id` / `label` / `date` (`YYYY-MM-DD`) / `weekday` / `time` |
| `notices[]` | `title` / `body` / `level` (`important` または `info`) |
| `forms[]` | `label` / `description` / `url` |
| `venue` | `mapImage` / `mapNote` / `resourceLinks[]` |
| `bookSale` | 任意。`url` / `label` / `note`。書籍特設販売ページへの導線 |

### タイムテーブルと書籍

| キー | 内容 |
| --- | --- |
| `rooms[]` | `id` / `name` / `color` |
| `sessions[]` | `id` / `dateId` / `start` / `end`（任意）/ `category` / `note`（任意）/ `items[]` |
| `sessions[].afterNote` | 任意。セッションカード直後に表示する補足 |
| `sessions[].items[]` | `room`（任意）/ `title`（任意）/ `meta[]` / `subtle`（任意） |
| `books[]` | `title` / `author` / `publisher` / `cover` / `description` / `url` / `amazon_url`（任意） |

会場色は `blue` / `blueDeep` / `green` / `greenDeep` / `orange` / `purple` を使用する。複数会場の並行プログラムは同じ時間帯の `items[]` にまとめる。

## 6. イベント追加手順

1. `events/<id>.json` を作成する。Excel ひな形を使う場合は `template/README.md` に従う。
2. `events.json` に `id` / `title` / `theme` / `dateRange` / `venueName` / `sortDate` / `brandColor` を追加する。
3. 会場図があれば `assets/venue-map-<id>.svg` 等を置き、`eventInfo.venue.mapImage` に指定する。外部公開 URL も使用できる。
4. PWA 名とアイコンを安定させる場合は `assets/icon-<id>.svg` と `events/<id>.webmanifest` を作り、`manifestPath` を設定する。
5. `python scripts/validate_events.py --event <id>` で、一覧との一致、日付ID・会場ID、URL、マニフェスト、アイコンを検証する。

AIで生成する場合は `template/event-data.schema.json` を出力契約として使用する。資料間の矛盾や未記載事項は推測で補わず、Excelの `要確認` シートで解決してからJSONを生成する。
v2 Excelからの生成は `scripts/import_event_workbook.py` を標準とし、既定の事前検証後に `--write` を明示して実行する。将来の形式差と品質指標は `docs/event-onboarding-review.md` に蓄積し、同ファイルの条件に達したらFormatを再レビューする。
6. 一覧、個別ページ、存在しない ID、モバイル表示、オフライン復帰を確認する。

## 7. 運用上の禁止・注意

- 過去の `events/<id>.json` を削除しない。一覧から外す場合は `events.json` のエントリだけを削除する
- 配布資料の PDF / Word 等はリポジトリに置かず、外部公開リンクを JSON に記述する
- フォームは PWA 内に実装せず、外部フォームへ誘導する
- 新規色クラスを動的生成する場合は Tailwind の設定と safelist を同期する
- 絵文字を UI アイコンとして使わず、既存の SVG / `ICONS` / `icon()` を利用する

## 8. 検証

```bash
python3 -m http.server 8080
python3 -m json.tool events.json
python3 -m json.tool events/<id>.json
```

Chrome DevTools の Application で、マニフェスト、Service Worker、キャッシュ、オフライン表示を確認する。
