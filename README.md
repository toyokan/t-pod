# t-pod — 教育イベント・研究会向け タイムテーブル PWA

教育イベント・研究会・授業研究大会などで、参加者がスマートフォンから
当日の**プログラム（タイムテーブル）**・**配布資料**・**関連書籍**を
スムーズに閲覧できる PWA（Progressive Web App）です。

- 会場の通信環境が不安定でも動作（Service Worker による Network First キャッシュ／オフライン対応）
- **UI とデータを完全分離**。新しいイベントはコードを触らず JSON を追加するだけで運用可能
- **マルチイベント対応**。`?id=<イベントID>` で読み込むデータを切り替え、過去イベントを永続保存
- **イベント毎にテーマ色を変更可能**。`eventInfo.brandColor` にメイン1色を指定するだけで全体の濃淡を自動生成
- **当日ナビゲーション**。開催期間中は当日の日付タブを自動選択し、タイムテーブルを現在時刻（進行中／直近のセッション）まで自動スクロール（当日以外は初日・先頭表示）
- **ホーム画面に追加できる PWA**。アプリ名・アイコンはイベント毎に実行時生成（名前＝`logoMain`、アイコン＝`brandColor` 地に `iconLabel`（未指定時は `logoMain` 先頭3文字））。アプリ内に追加導線（Android/iOS 対応）も表示
- **一覧ページ（`?id` 無し）の favicon は東洋館出版社サイト（www.toyokan.co.jp）と同一**（`index.html` の `<link rel="icon">` が直接参照）。イベントページでは前述の実行時生成アイコンに切り替わる
- 静的サイトのため GitHub Pages でそのまま公開可能

## マルチイベント方式（クエリパラメータ）

ひとつの `index.html` を使い回し、URL の `?id=` で表示するイベントを切り替えます。

| URL | 表示 |
| --- | --- |
| `https://<user>.github.io/t-pod/` | **イベント一覧**（`events.json` の内容をカード表示） |
| `https://<user>.github.io/t-pod/?id=2026-zensanken-37` | 当該イベントのプログラム／資料／書籍 |

過去イベントの JSON（`events/<id>.json`）はリポジトリに残し続けるため、
**当時のチラシ（QRコード）の `?id=...` リンクは将来もそのまま有効**です。

## ファイル構成

```text
/ (リポジトリ直下)
├── index.html       # 汎用 UI シェル（一覧モード / イベントモードを id で切替）
├── events.json      # 全イベントのインデックス（一覧表示・新規追加の起点）
├── events/          # イベントごとの詳細データ
│   ├── 2026-zensanken-37.json           # 第37回 全国算数授業研究大会
│   ├── 2026-zensanken-37.webmanifest    # イベント別 実体マニフェスト
│   ├── 2026-zenkokuken-27.json          # 第27回 全国国語授業研究大会
│   ├── 2026-zenkokuken-27.webmanifest
│   └── 2026-math-summer-fes.json        # オール筑波 算数サマーフェスティバル2026
├── manifest.json    # PWA インストール用マニフェスト
├── sw.js            # Service Worker（Network First キャッシュ）
└── assets/          # アイコン・会場マップ等の静的ファイル
    ├── icon.svg                          # PWA ホーム画面アイコン（manifest.json から参照）
    ├── favicon.svg                       # 未使用の予備ファイル（現在の一覧ページ favicon は東洋館サイトの画像を直接参照）
    ├── icon-2026-zensanken-37.svg        # イベント別 PWA アイコン
    ├── icon-2026-zenkokuken-27.svg
    └── venue-map-2026-zensanken-37.svg   # イベント別 会場マップ
```

## ローカルでの確認

静的サーバが必要です（`file://` 直開きでは fetch / Service Worker が動きません）。

```bash
python3 -m http.server 8080
# → ブラウザで http://localhost:8080/ を開く
```

PWA の動作確認は Chrome DevTools の **Application** タブで、
manifest の認識・Service Worker の登録・オフライン表示を確認できます。

## GitHub Pages での公開

1. リポジトリの **Settings → Pages** を開く
2. **Source** を `Deploy from a branch` にし、Branch を `main` / `/ (root)` に設定
3. 数分後、`https://<ユーザー名>.github.io/t-pod/` で公開されます

> パスはすべて相対指定のため、サブパス配信（`/t-pod/`）でも追加設定は不要です。

## 設計方針：UI と「個別の研究会情報」を完全分離

別の研究会・イベントのページを起こすときも **JSON を追加するだけ**で済むよう、
個別情報は **すべて `events/<id>.json` と `events.json` に集約**しています。

| ファイル | 役割 | 研究会ごとに編集するか |
| --- | --- | --- |
| `index.html` | **汎用** の UI シェル・描画ロジック。固有の文言は持たない（タイトル等は JSON から動的反映） | ❌ 触らない |
| `sw.js` | 汎用のキャッシュ制御 | ❌ 触らない（ロジック変更時のみ `CACHE_VERSION` を更新） |
| `manifest.json` | PWA の汎用シェル（インストール名・テーマ色など） | △ 任意（インストール名を変えたい場合のみ） |
| **`events/<id>.json`** | **個別の研究会情報（イベント名・テーマ・プログラム・資料・書籍）** | ✅ ここを追加・編集 |
| **`events.json`** | **イベント一覧（インデックス）** | ✅ 1エントリ追記 |
| `assets/` | アイコン・会場マップ画像 | △ 任意（画像を差し替える場合のみ） |

## 運用フロー：新しいイベントの追加

コード（`index.html` / `sw.js`）は一切触りません。

1. **`events/<新id>.json` を作成**（既存の JSON を複製して中身を書き換え／企画書テキストから Claude が生成）。
   `<新id>` は半角英数・ハイフン・アンダースコアのみ（例: `2026-autumn`）。
2. **`events.json` の `events[]` に1エントリ追記**（`id` / `title` / `theme` / `dateRange` / `venueName` / `sortDate`）。
3. **チラシのQRコードに `?id=<新id>` を付与**（例: `https://<user>.github.io/t-pod/?id=2026-autumn`）。
4. **会場マップ（任意・イベント別）**: 会場はイベント毎に異なるため、`events/<新id>.json` の `eventInfo.venue.mapImage` で切り替える。
   - リポジトリ内図: `assets/venue-map-<新id>.svg`（または `.png`/`.jpg`）として置き、相対パスで指定（アイコンの `icon-<id>.svg` と同じ命名で統一）。
   - 外部リンク: 会場図の写真等は公開URL（Google Drive 等）を `mapImage` に直接指定でも可。
   - 不要なら `mapImage` を省略（`mapNote` テキストのみ表示）。
5. （PWA 名・アイコンを確実に出したい場合）**実体マニフェストとブランドアイコンを用意**:
   - `assets/icon-<新id>.svg`（`brandColor` 地に `logoMain` 先頭3文字。`assets/icon-2026-zensanken-37.svg` を複製して色・文字を変更）。
   - `events/<新id>.webmanifest`（`name`/`short_name`＝`logoMain`、`theme_color`＝`brandColor`、`start_url`＝`../?id=<新id>`、`icons`＝上記 SVG）。
   - `events/<新id>.json` の `eventInfo.manifestPath` に `events/<新id>.webmanifest` を指定。
   - シェル（`sw.js`）変更は不要だが、新アイコンを `sw.js` の `APP_SHELL` に追記すると初回オフラインでも表示可（任意）。

> 企画書（Word 等）のテキストを Claude に渡し、
> 「このテキストから `events/<id>.json` を生成し、`events.json` に追記せよ」と指示するだけで更新できます。
>
> JSON に不慣れな担当者向けに **Excel 入力ひな形** を用意しています（`template/イベント情報入力シート.xlsx`）。
> 記入ルールと Claude への変換依頼手順は [`template/README.md`](template/README.md) を参照してください。

### `events.json` のスキーマ

| キー | 内容 |
| --- | --- |
| `siteTitle` / `siteSubtitle` | 一覧ページ（`?id` 無し）のヘッダー文言 |
| `events[]` | `id`（= `events/<id>.json` のファイル名）/ `title` / `theme` / `dateRange` / `venueName` / `sortDate`（`YYYY-MM-DD`、新しい順に表示）/ `brandColor`（任意・各カードのアクセント色。個別ページの `eventInfo.brandColor` と揃える） |

> 一覧ページ自体の基調色は**東洋館出版社のイメージカラー（イエロー `#ffd900`）**（`<style>` の `:root { --brand }` 既定値）。
> 各イベントカードは `events[].brandColor` を `--brand` に上書きして**カード単位でそのイベント固有色**に切り替わります（個別ページを開くと同色）。

### `events/<id>.json` のスキーマ

| キー | 内容 |
| --- | --- |
| `eventInfo.title` | イベント名（ヘッダー・タブタイトル・PWA タイトルに反映） |
| `eventInfo.subtitle` | ヘッダー副題（会場名など） |
| `eventInfo.theme` | 大会／研究会テーマ（プログラム上部のバナーと概要に表示） |
| `eventInfo.venueName` / `eventInfo.dateRange` | 概要（🔔 FAB）に表示する会場名・会期 |
| `eventInfo.tagline` | 主催名などの短いキャッチ（任意） |
| `eventInfo.logoMain` / `eventInfo.logoSub` | ヘッダーのロゴ表示用テキスト（大＝`logoMain`／小＝`logoSub`。未指定時は `title` / `subtitle` を使用）。**ホーム画面追加（PWA）時のアプリ名＝`logoMain`（例: 全算研2026）、アイコン＝`brandColor` 地に `logoMain` の先頭3文字（例: 全算研）**を実行時生成 |
| `eventInfo.iconLabel` | **PWA アイコン文字をヘッダー表示（`logoMain`）と別にしたい場合**の任意フィールド（例: `logoMain`＝「算数サマー2026」・`iconLabel`＝「算サマ」）。指定時はアイコン生成にこちらを優先使用（先頭3文字ルールは変わらず適用）。未指定時は従来通り `logoMain` 先頭3文字 |
| `eventInfo.brandColor` | **イベントのテーマ（アクセント）色**。メイン1色を16進で指定（例 `#f59e0b`）。濃淡は自動生成。任意（未指定時は既定の amber） |
| `eventInfo.manifestPath` | **ホーム画面追加（PWA）の名前・アイコンを確実に出すための実体マニフェスト**へのパス（`events/<id>.webmanifest`）。任意だが推奨。未指定時は実行時生成の data URI マニフェストにフォールバック（iOS で不安定なことがある） |
| `eventInfo.dates[]` | `id` / `label` / `date`（`YYYY-MM-DD`）/ `weekday` / `time`。日付切替タブと当日の時間帯表示に使用。`date` が閲覧端末の**今日**と一致する日は、そのタブが既定選択され、タイムテーブルが現在時刻まで自動スクロールする |
| `eventInfo.notices[]` | `title` / `body` / `level`（`important` または `info`）。🔔 FAB の概要・お知らせに表示 |
| `eventInfo.forms[]` | `label` / `description` / `url`。「資料」タブの外部フォームリンク |
| `eventInfo.venue` | `mapImage` / `mapNote` / `resourceLinks[]`（配布資料リンク）。**会場はイベント毎に異なるため会場マップもイベント単位で差し替え可**。`mapImage` に `assets/venue-map-<id>.svg`（`.png`/`.jpg` 可）か外部公開URL（Google Drive 等）を指定。省略時は画像非表示で `mapNote` のみ表示（取得失敗時も画像だけ非表示で崩れない） |
| `rooms[]` | `id` / `name` / `color`。会場ラベルの色分けに使用（彩度をそろえた専用パレット）。淡色＝`blue` `green` `orange` `purple`、濃色（塗りつぶし＋白文字）＝`blueDeep` `greenDeep`。同建物内で複数の部屋を「濃／淡」で区別する用途に使用。会場マップSVG（`venue-map-<id>.svg`）の配色もこのパレットに揃えると FILES タブと TIMETABLE タブで色が一致する |
| `sessions[]` | `id` / `dateId` / `start` / `end`（`H:MM`、`end` は任意）/ `category`（内容）/ `note`（任意）/ `items[]` |
| `sessions[].items[]` | `room`（任意・会場ラベル）/ `title`（任意）/ `meta[]`（授業者・児童・司会などの行） |
| `books[]` | `title` / `author` / `publisher` / `cover` / `description` / `url` / `amazon_url`（任意・`url` 未指定時のリンク先フォールバック） |

プログラムは「時間 → 内容（`category`）→ 詳細（`items`）」の縦型タイムラインで表示されます。
全体会は `items` に `room` を付けず、分科会など複数会場がある時間帯は `items` に `room`（例: `A会場`）を付けた要素を並べてください。

### 注意事項

- 個別の研究会情報は **すべて `events/<id>.json` と `events.json`** に記述します。`index.html` には固有の文言を書かないでください。
- 過去イベントの `events/<id>.json` は削除しないでください（旧チラシのQRリンクが無効になります）。`events.json` の一覧から外すだけなら `?id=...` 直リンクは生き続けます。
- PDF・Word などの配布資料ファイル自体はリポジトリに含めず、
  Google Drive 等の**外部公開リンク**を `items[].meta` / `resourceLinks` に記述してください（容量対策）。
- アンケート等のフォームは PWA 内では処理せず、Google フォーム等の外部 URL へ誘導します。
- `sw.js` のロジックやアプリシェルを変更した場合は、`CACHE_VERSION` を上げてください。

## License

本リポジトリに含まれる文章、画像、ロゴ、書影その他のコンテンツの
著作権は、各権利者に帰属します。許可なく転載・再配布することを禁じます。
