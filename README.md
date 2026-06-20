# t-pod — 教育イベント・研究会向け タイムテーブル PWA

算数春の祭典などの教育イベント／研究会で、参加者がスマートフォンから
当日の**プログラム（タイムテーブル）**・**配布資料**・**関連書籍**を
スムーズに閲覧できる PWA（Progressive Web App）です。

- 会場の通信環境が不安定でも動作（Service Worker による Network First キャッシュ／オフライン対応）
- **UI とデータを完全分離**。次回開催時はコードを触らず `data.json` の差し替えだけで運用可能
- 静的サイトのため GitHub Pages でそのまま公開可能

## ファイル構成

```text
/ (リポジトリ直下)
├── index.html       # UI 構造 + 描画ロジック（SPA）
├── data.json        # イベント全情報（← 更新するのはここだけ）
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

別の研究会・イベントのページを起こすときも **`data.json` を差し替えるだけ**で済むよう、
個別情報は **すべて `data.json` に集約**しています。

| ファイル | 役割 | 研究会ごとに編集するか |
| --- | --- | --- |
| `index.html` | **汎用** の UI シェル・描画ロジック。固有の文言は持たない（タイトル等は `data.json` から動的反映） | ❌ 触らない |
| `sw.js` | 汎用のキャッシュ制御 | ❌ 触らない（ロジック変更時のみ `CACHE_VERSION` を更新） |
| `manifest.json` | PWA の汎用シェル（インストール名・テーマ色など） | △ 任意（インストール名を変えたい場合のみ） |
| **`data.json`** | **個別の研究会情報（イベント名・テーマ・プログラム・資料・書籍）** | ✅ ここだけ編集 |
| `assets/` | アイコン・会場マップ画像 | △ 任意（画像を差し替える場合のみ） |

## 運用フロー：イベントごとの更新

**`data.json` を差し替えるだけ**で中身を更新できます。HTML / JS の編集は不要です。

> 企画書（Word 等）のテキストを Claude に渡し、
> 「このテキストから最新の `data.json` を生成して上書きせよ」と指示するだけで更新できます。

### `data.json` のスキーマ

| キー | 内容 |
| --- | --- |
| `eventInfo.title` | イベント名（ヘッダー・タブタイトル・PWA タイトルに反映） |
| `eventInfo.subtitle` | ヘッダー副題（会場名など） |
| `eventInfo.theme` | 大会／研究会テーマ（プログラム上部のバナーと概要に表示） |
| `eventInfo.venueName` / `eventInfo.dateRange` | 概要（🔔 FAB）に表示する会場名・会期 |
| `eventInfo.tagline` | 主催名などの短いキャッチ（任意） |
| `eventInfo.dates[]` | `id` / `label` / `date` / `weekday` / `time`。日付切替タブと当日の時間帯表示に使用 |
| `eventInfo.notices[]` | `title` / `body` / `level`（`important` または `info`）。🔔 FAB の概要・お知らせに表示 |
| `eventInfo.forms[]` | `label` / `description` / `url`。「資料」タブの外部フォームリンク |
| `eventInfo.venue` | `mapImage` / `mapNote` / `resourceLinks[]`（配布資料リンク） |
| `rooms[]` | `id` / `name` / `color`（`blue` `green` `orange` `purple` `red`）。会場ラベルの色分けに使用 |
| `sessions[]` | `id` / `dateId` / `start` / `end`（`H:MM`、`end` は任意）/ `category`（内容）/ `note`（任意）/ `items[]` |
| `sessions[].items[]` | `room`（任意・会場ラベル）/ `title`（任意）/ `meta[]`（授業者・児童・司会などの行） |
| `books[]` | `title` / `author` / `publisher` / `cover` / `description` / `url` |

プログラムは「時間 → 内容（`category`）→ 詳細（`items`）」の縦型タイムラインで表示されます。
全体会は `items` に `room` を付けず、分科会など複数会場がある時間帯は `items` に `room`（例: `A会場`）を付けた要素を並べてください。

### 注意事項

- 個別の研究会情報は **すべて `data.json`** に記述します。`index.html` には固有の文言を書かないでください。
- PDF・Word などの配布資料ファイル自体はリポジトリに含めず、
  Google Drive 等の**外部公開リンク**を `items[].meta` / `resourceLinks` に記述してください（容量対策）。
- アンケート等のフォームは PWA 内では処理せず、Google フォーム等の外部 URL へ誘導します。
- `sw.js` のロジックやアプリシェルを変更した場合は、`CACHE_VERSION` を上げてください。
