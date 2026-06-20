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

## 運用フロー：イベントごとの更新

**`data.json` を差し替えるだけ**で中身を更新できます。HTML / JS の編集は不要です。

> 企画書（Word 等）のテキストを Claude に渡し、
> 「このテキストから最新の `data.json` を生成して上書きせよ」と指示するだけで更新できます。

### `data.json` のスキーマ

| キー | 内容 |
| --- | --- |
| `eventInfo` | イベント名・開催日リスト・お知らせ・フォーム・会場/資料情報 |
| `eventInfo.dates[]` | `id` / `label` / `date` / `weekday`。日付切替タブに使用 |
| `eventInfo.notices[]` | `title` / `body` / `level`（`important` または `info`）。FAB のお知らせに表示 |
| `eventInfo.forms[]` | `label` / `description` / `url`。「資料」タブの外部フォームリンク |
| `eventInfo.venue` | `mapImage` / `mapNote` / `resourceLinks[]`（配布資料リンク） |
| `rooms[]` | `id` / `name` / `subtitle` / `color`（`blue` `green` `orange` `purple` `red`） |
| `sessions[]` | `id` / `dateId` / `start` / `end`（`HH:MM`）/ `roomId` / `title` / `speaker` / `description` / `materialUrl` / `status[]` |
| `books[]` | `title` / `author` / `publisher` / `cover` / `description` / `url` |

`sessions[].status` に指定できる値: `full`（満席 🈵）/ `few`（残席わずか ⚠️）/ `material`（資料配布あり 📄）

### 注意事項

- PDF・Word などの配布資料ファイル自体はリポジトリに含めず、
  Google Drive 等の**外部公開リンク**を `materialUrl` / `resourceLinks` に記述してください（容量対策）。
- アンケート等のフォームは PWA 内では処理せず、Google フォーム等の外部 URL へ誘導します。
- `sw.js` のロジックやアプリシェルを変更した場合は、`CACHE_VERSION` を上げてください。
