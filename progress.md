# 開発の記録（progress.md）

このPWAの開発経緯・現状・残課題のログです。新しい作業を行ったら追記してください。

## 現状サマリ
- **マルチイベント対応のタイムテーブル PWA が完成**し、`main` にマージ済み。
- 公開URL（GitHub Pages 有効化後）:
  - イベント一覧: `https://<user>.github.io/t-pod/`
  - 個別イベント: `https://<user>.github.io/t-pod/?id=2026-zensanken-37`
- 現在登録されているイベント: **第37回 全国算数授業研究大会**（`events/2026-zensanken-37.json`、amber `#f59e0b`）／**第27回 全国国語授業研究大会**（`events/2026-zenkokuken-27.json`、シアン `#00a7d8`）の2件。
- 現在のデザイン: ロゴ調のコンパクトなヘッダー、フッターは **TIMETABLE / FILES / BOOKS** の3タブ。テーマ色は `eventInfo.brandColor` で**イベント毎に変更可能**（濃淡は自動生成）。**一覧ページの基調色は東洋館イメージカラーのイエロー `#ffd900`**、一覧の各カードは `events[].brandColor` でイベント固有色に切替。

## マイルストーン（PR単位）

### PR #1 — 初期PWA構築（merged）
- ディレクトリ構成・レスポンシブUI（Tailwind CDN）・JSONパース・Service Worker を実装。
- ボトムナビ3タブ（プログラム / 資料 / 書籍）、Sticky ヘッダー、FAB、各種モーダル。
- Service Worker による Network First キャッシュ（オフライン対応）。
- サンプル `data.json`（架空イベント）を同梱。

### PR #2 — 実データ反映 + UI 汎用化（merged）
- 第37回 全国算数授業研究大会の実データ（テーマ・会期・会場・1〜2日目の全プログラム・登壇者・2日目ワークショップ案内）を反映。
- タイムテーブルを **room×time グリッド → 縦型タイムライン**（時間 → 内容 → 詳細）に変更。全体会中心＋一部 A〜D 会場の分科会に対応。
- `index.html` から固有文言を排除し、タイトル等を JSON から動的反映する**汎用シェル化**。`manifest.json` も汎用名に。

### PR #3 — マルチイベント対応（merged）
- `?id=<id>` クエリパラメータ方式を導入。`events/<id>.json` にイベント詳細を集約（旧 `data.json` を `events/2026-zensanken-37.json` に移設）。
- `events.json`（一覧インデックス）を追加。`?id` 無しのルートURLは一覧表示。
- `sw.js` の precache を `data.json` → `events.json` に変更、`CACHE_VERSION` を v3 に。
- 目的: **過去のチラシ（QR）からアクセスしても当時の情報が永続的に見られる**ようにする。

### ドキュメント整備
- `CLAUDE.md`（プロジェクトガイド）と `progress.md`（本ファイル）を追加。

### デザインのモダン化
- カラーシステム整理: アクセント色を `brand`（indigo）として `tailwind.config` に定義。会場色を blue/emerald/amber/violet/rose に統一し、`COLOR` 辞書を `chip`/`dot`/`border` に再編。
- 絵文字を廃止し **SVGアイコン（Lucide系）** に置換（`ICONS` + `icon()` ヘルパ）。ボトムナビ・FAB・リンク・書籍・モーダルなど全面。
- UI刷新: グラデーションヘッダー、角丸カード＋ソフトシャドウ、タイムラインのドットレール表示、フェードイン演出（`prefers-reduced-motion` 対応）。

### PR #7 — ヘッダー/フッターのリデザイン（merged）
- テーマカラーを indigo → **オレンジ寄りの黄色（amber 系 `#f59e0b`）** に変更。`tailwind.config` の `brand` パレット1か所差し替えで全体へ波及。`<meta name="theme-color">`・`manifest.json` の `theme_color` も更新。
- ヘッダーを**ロゴ調**に変更。ロゴ文言は `eventInfo.logoMain`/`logoSub` で **JSON 駆動化**（未指定時は `title`/`subtitle` にフォールバック、`document.title` は正式名 `title` を維持）。
- **日付切替タブをヘッダーからタイムテーブル表示内（`view-program`）へ移動**。白背景向けに配色変更。
- フッターを **TIMETABLE / FILES / BOOKS の3タブ**に刷新（内部 `data-tab`・view ID は流用）。アクティブはピル形状（薄オレンジ背景＋濃オレンジ）、非アクティブはグレー。
- シェル変更に伴い `sw.js` の `CACHE_VERSION` を v5 に。

### PR #8〜#10 — ヘッダーの微調整（merged）
- **#8**: ヘッダー文字をセンター揃え。ヘッダー/フッターの最大幅を `max-w-3xl` → `max-w-2xl` に縮小・中央寄せ。ヘッダー下端を `rounded-b-2xl` に。
- **#9**: ヘッダーの幅をさらに縮小（`max-w-2xl` → `max-w-md`）。
- **#10**: ヘッダーの高さを縮小（縦パディング `pt-4 pb-3.5` → `pt-2.5 pb-2`、ロゴ `text-3xl` → `text-2xl`、サブ `text-sm` → `text-xs`）。
- 各 PR でシェル変更に合わせ `sw.js` の `CACHE_VERSION` を v6 → v7 → v8 へ順次更新。

### PR #11 — イベント毎ブランドカラー対応＋会場カラーの統一（open）
- **ブランド色のイベント毎指定**: `brand` パレットを **CSS 変数 `--brand` 基準の `color-mix()`** 化し、メイン1色から `brand-50〜800` を自動生成。`events/<id>.json` の `eventInfo.brandColor`（16進1色）を `applyBrandColor()` が実行時に `--brand` へ適用（`<meta name="theme-color">` も同期、不正値は既定 amber にフォールバック）。既定値は `<style>` の `:root { --brand: #f59e0b }`。
- ハードコードされていた `amber-*` アクセント（テーマバナー・お知らせ）を `brand-*` に統一。
- **会場カラーの統一**: 検証により、`tailwind.config` の `venue.*` パレット＋ `bg-venue-*` safelist が**未使用**で、描画する `COLOR` 辞書が safelist 外の標準色を参照していた不整合を発見。`COLOR` 辞書を `venue.*` へ接続（`blue→venue-blue` / `green→venue-green` / `orange→venue-coral` / `purple→venue-violet`）、未使用の `red` を削除。ブランド amber と C会場の色相衝突も解消。
- `safelist` に `brand-*` クラスを追加。`README.md` / `CLAUDE.md` に色設定の仕様を追記。`sw.js` の `CACHE_VERSION` を v9 に。

### 会場マップのイベント別命名対応
- 会場はイベント毎に異なるため、会場マップもイベント単位で差し替えられるよう運用を整理。**仕組み自体は既存**（`eventInfo.venue.mapImage` を `renderMaterials()` が読み込み。パス/外部URL両対応、未指定時は画像非表示で `mapNote` のみ）。
- 汎用名 `assets/venue-map.svg`（中身は筑波大附属小専用）を、アイコン（`icon-<id>.svg`）と同じイベント別命名 `assets/venue-map-2026-zensanken-37.svg` に **git mv でリネーム**。`events/2026-zensanken-37.json` の `mapImage` を新パスに更新。
- `CLAUDE.md`／`README.md`／`template/README.md` に「イベント別会場マップの命名・運用ルール」を追記。`index.html`・`sw.js` は不変（シェル変更なしのため `CACHE_VERSION` 更新不要）。

### 第27回 全国国語授業研究大会の追加
- Excel入力シート（`イベント情報入力シート2026-zenkokuken-27`）から `events/2026-zenkokuken-27.json` を新規生成（eventInfo／rooms／sessions 16本／notices／forms／books 7冊）。並行行（公開授業II・協議会のA/B会場、教材別ワークショップⅠ/Ⅱ各8本、テーマ別ワークショップ10本）は1セッションの `items[]` に集約。
- `events.json` に1エントリ追記（計2件）。実体マニフェスト `events/2026-zenkokuken-27.webmanifest` とブランドアイコン `assets/icon-2026-zenkokuken-27.svg`（背景 `#00a7d8`・文字「全国研」）を追加。
- 申込みリンクを本番URLに更新（東洋館オンラインショップ `products/27kokugojyugyouken`／Peatix `27kokugojyugyouken.peatix.com/view`）。
- 会場マップ画像はシート未指定のため `mapImage` 省略（`mapNote` のみ）。

### 一覧ページの東洋館カラー化＋カード個別色
- 一覧ページの基調色（`:root { --brand }` 既定値）を **東洋館イメージカラーのイエロー `#ffd900`** に変更。
- `events.json` の各エントリに `brandColor` を追加し、`renderEventList()` でカードごとに `card.style.setProperty("--brand", …)` を設定。`brand-*`（`color-mix` ベース）が再計算され、**カード単位でイベント固有色**（全国研＝シアン／全算研＝amber）に。シェル変更のため `sw.js` の `CACHE_VERSION` を v18→v19 に更新。

### 当日ナビゲーション（日付タブ自動選択＋現在時刻スクロール）
- **当日タブの既定表示**: `renderDateTabs()` の初期選択を「常に初日」から「今日と一致する `eventInfo.dates[].date`（`YYYY-MM-DD`）があればその日、なければ初日」に変更。判定は閲覧端末のローカル日付。ユーザーが手動でタブを切り替えれば `activeDateId` が優先される。
- **現在時刻へ自動スクロール**: `renderTimetable()` に、当日のみ「現在時刻 ≤ `start` を満たす最後のセッション（＝進行中／直近）」を判定し、`scrollIntoView({ block:"center" })` で自動スクロール＋対象カードに `ring-2 ring-brand-500` の枠を付与する処理を追加。当日以外・全枠が未開始の場合は何もしない（従来通り先頭表示）。
- シェル変更のため `sw.js` の `CACHE_VERSION` を v19→v20 に更新。

### 全算研の会場配色調整
- rooms の濃淡入れ替え: 1音 `greenDeep`→`green`（淡）、2音 `green`→`greenDeep`（濃）。
- 会場マップSVG（`venue-map-2026-zensanken-37.svg`）の配色を TIMETABLE タブの会場色に統一（講堂＝濃青／1体＝淡青／1音＝淡緑／2音＝濃緑）。修正前は1体＝コーラル・1音＝バイオレットで不一致だった。`index.html`・`sw.js` は不変。

## 残課題 / TODO
- [ ] **GitHub Pages の有効化**（Settings → Pages → main / root）。
- [ ] **判読困難だった氏名・所属の確認**（画像から転記したもの）:
  - 2日目ワークショップ案内の登壇者・所属（例: 山本良一／島根・雲南市立木次小、髙木美和／福岡・赤村立赤小 など）。
  - シンポジウム討論者「久保田健功」の表記。
  - 修正は `events/2026-zensanken-37.json` の該当箇所のみ。
- [ ] （任意）QRコード生成の仕組み。
- [ ] （任意）書籍データの拡充（実際の販売書籍リスト）。
- [ ] （任意）会場マップ画像（`assets/venue-map-2026-zensanken-37.svg`）の本番図面への差し替え。
- [ ] （任意）PWAアイコン（`assets/icon.svg`）の本番デザインへの差し替え。
