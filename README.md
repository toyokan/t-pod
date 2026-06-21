# t-pod — 教育イベント・研究会向け タイムテーブル PWA

算数春の祭典などの教育イベント／研究会で、参加者がスマートフォンから
当日の**プログラム（タイムテーブル）**・**配布資料**・**関連書籍**を
スムーズに閲覧できる PWA（Progressive Web App）です。

- 会場の通信環境が不安定でも動作（Service Worker による Network First キャッシュ／オフライン対応）
- **UI とデータを完全分離**。新しいイベントはコードを触らず JSON を追加するだけで運用可能
- **マルチイベント対応**。`?id=<イベントID>` で読み込むデータを切り替え、過去イベントを永続保存
- **イベント毎にテーマ色を変更可能**。`eventInfo.brandColor` にメイン1色を指定するだけで全体の濃淡を自動生成
- **ホーム画面に追加できる PWA**。アプリ名・アイコンはイベント毎に実行時生成（名前＝`logoSub`、アイコン＝`brandColor`＋`logoMain`）。アプリ内に追加導線（Android/iOS 対応）も表示
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
│   └── 2026-zensanken-37.json
├── manifest.json    # PWA インストール用マニフェスト
├── sw.js            # Service Worker（Network First キャッシュ）
└── assets/          # アイコン・会場マップ等の静的ファイル
    ├── icon.svg
    ├── favicon.svg
    └── venue-map.svg
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
4. （PWA 名・アイコンを確実に出したい場合）**実体マニフェストとブランドアイコンを用意**:
   - `assets/icon-<新id>.svg`（`brandColor` 地に `logoMain` 文字。`assets/icon-2026-zensanken-37.svg` を複製して色・文字を変更）。
   - `events/<新id>.webmanifest`（`name`/`short_name`＝`logoSub`、`theme_color`＝`brandColor`、`start_url`＝`../?id=<新id>`、`icons`＝上記 SVG）。
   - `events/<新id>.json` の `eventInfo.manifestPath` に `events/<新id>.webmanifest` を指定。
   - シェル（`sw.js`）変更は不要だが、新アイコンを `sw.js` の `APP_SHELL` に追記すると初回オフラインでも表示可（任意）。

> 企画書（Word 等）のテキストを Claude に渡し、
> 「このテキストから `events/<id>.json` を生成し、`events.json` に追記せよ」と指示するだけで更新できます。

### `events.json` のスキーマ

| キー | 内容 |
| --- | --- |
| `siteTitle` / `siteSubtitle` | 一覧ページ（`?id` 無し）のヘッダー文言 |
| `events[]` | `id`（= `events/<id>.json` のファイル名）/ `title` / `theme` / `dateRange` / `venueName` / `sortDate`（`YYYY-MM-DD`、新しい順に表示） |

### `events/<id>.json` のスキーマ

| キー | 内容 |
| --- | --- |
| `eventInfo.title` | イベント名（ヘッダー・タブタイトル・PWA タイトルに反映） |
| `eventInfo.subtitle` | ヘッダー副題（会場名など） |
| `eventInfo.theme` | 大会／研究会テーマ（プログラム上部のバナーと概要に表示） |
| `eventInfo.venueName` / `eventInfo.dateRange` | 概要（🔔 FAB）に表示する会場名・会期 |
| `eventInfo.tagline` | 主催名などの短いキャッチ（任意） |
| `eventInfo.logoMain` / `eventInfo.logoSub` | ヘッダーのロゴ表示用テキスト（任意。未指定時は `title` / `subtitle` を使用）。**ホーム画面追加（PWA）時のアプリ名＝`logoSub`、アイコン＝`brandColor` 地に `logoMain` の文字**を実行時生成 |
| `eventInfo.brandColor` | **イベントのテーマ（アクセント）色**。メイン1色を16進で指定（例 `#f59e0b`）。濃淡は自動生成。任意（未指定時は既定の amber） |
| `eventInfo.manifestPath` | **ホーム画面追加（PWA）の名前・アイコンを確実に出すための実体マニフェスト**へのパス（`events/<id>.webmanifest`）。任意だが推奨。未指定時は実行時生成の data URI マニフェストにフォールバック（iOS で不安定なことがある） |
| `eventInfo.dates[]` | `id` / `label` / `date` / `weekday` / `time`。日付切替タブと当日の時間帯表示に使用 |
| `eventInfo.notices[]` | `title` / `body` / `level`（`important` または `info`）。🔔 FAB の概要・お知らせに表示 |
| `eventInfo.forms[]` | `label` / `description` / `url`。「資料」タブの外部フォームリンク |
| `eventInfo.venue` | `mapImage` / `mapNote` / `resourceLinks[]`（配布資料リンク） |
| `rooms[]` | `id` / `name` / `color`（`blue` `green` `orange` `purple`）。会場ラベルの色分けに使用（彩度をそろえた専用パレット） |
| `sessions[]` | `id` / `dateId` / `start` / `end`（`H:MM`、`end` は任意）/ `category`（内容）/ `note`（任意）/ `items[]` |
| `sessions[].items[]` | `room`（任意・会場ラベル）/ `title`（任意）/ `meta[]`（授業者・児童・司会などの行） |
| `books[]` | `title` / `author` / `publisher` / `cover` / `description` / `url` |

プログラムは「時間 → 内容（`category`）→ 詳細（`items`）」の縦型タイムラインで表示されます。
全体会は `items` に `room` を付けず、分科会など複数会場がある時間帯は `items` に `room`（例: `A会場`）を付けた要素を並べてください。

### 注意事項

- 個別の研究会情報は **すべて `events/<id>.json` と `events.json`** に記述します。`index.html` には固有の文言を書かないでください。
- 過去イベントの `events/<id>.json` は削除しないでください（旧チラシのQRリンクが無効になります）。`events.json` の一覧から外すだけなら `?id=...` 直リンクは生き続けます。
- PDF・Word などの配布資料ファイル自体はリポジトリに含めず、
  Google Drive 等の**外部公開リンク**を `items[].meta` / `resourceLinks` に記述してください（容量対策）。
- アンケート等のフォームは PWA 内では処理せず、Google フォーム等の外部 URL へ誘導します。
- `sw.js` のロジックやアプリシェルを変更した場合は、`CACHE_VERSION` を上げてください。
