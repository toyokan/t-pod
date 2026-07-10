# 開発の記録（progress.md）

このPWAの開発経緯・現状・残課題のログです。新しい作業を行ったら追記してください。

## 現状サマリ
- **マルチイベント対応のタイムテーブル PWA が完成**し、`main` にマージ済み。
- 公開URL（GitHub Pages 有効化後）:
  - イベント一覧: `https://<user>.github.io/t-pod/`
  - 個別イベント: `https://<user>.github.io/t-pod/?id=2026-zensanken-37`
- 現在登録されているイベント: **第37回 全国算数授業研究大会**（`events/2026-zensanken-37.json`、amber `#f59e0b`）／**第27回 全国国語授業研究大会**（`events/2026-zenkokuken-27.json`、シアン `#00a7d8`）／**オール筑波 算数サマーフェスティバル2026**（`events/2026-math-summer-fes.json`、スカイブルー `#0ea5e9`）の3件。
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

### 品質・アクセシビリティ改善 + リポジトリ監査
- **当日ライブUX**: 「現在」ハイライトが1分毎に自動追従（`updateNowMarker()` + `setInterval`、タブ復帰時は `visibilitychange` で即時更新）。従来は描画時に一度だけ計算され時間経過に追従しなかった。進行中セッションに「進行中」バッジ（パルスドット）を追加。自動スクロールは初回描画のみに変更（従来は日付タブ切替のたびに発火し操作を妨げていた）。当日タブに目印ドットを追加。
- **ローディング/オフラインUX**: 初期表示にスケルトンローディングを追加（従来は「読み込み中…」テキストのみ）。オフライン時のバナー表示を追加。
- **safe-area対応**: ヘッダー（`padding-top: env(safe-area-inset-top)`）・FAB（`env(safe-area-inset-bottom)`）がノッチ端末で欠けていたのを修正。
- **コンテナ幅統一**: ヘッダー`max-w-md`／メイン`max-w-3xl`／ナビ`max-w-2xl`のバラつきを `max-w-2xl` に統一。
- **アクセシビリティ**: ボトムナビに `aria-current`、日付タブに `aria-pressed`、モーダルに `role="dialog"`/`aria-modal` とフォーカス管理（開閉時のフォーカス移動・復帰）を追加。
- **書籍cover空白バグ**: `cover: " "`（空白のみ）が truthy 判定されて無駄な画像リクエスト→エラー→プレースホルダ差し替えが発生していたのを trim 判定で修正。`amazon_url` を `url` 未指定時のリンク先フォールバックとして活用（従来は取得のみでリンクに未使用）。
- **sw.js プリキャッシュ不整合の解消**: `APP_SHELL` が実在しない `assets/venue-map.svg`（毎回404）と特定イベントの `icon-2026-zensanken-37.svg` をハードコードしていたのを削除。イベント別アセットは Network First のオンデマンドキャッシュに委譲し、新イベント追加時に `sw.js` を触る必要をなくした。
- **キャッシュ名の汎用化**: `CACHE_NAME` が旧「算数フェス」由来の `sansu-fes-*` だったのを `t-pod-*` に変更（汎用シェル方針に合わせる）。activate 時に旧接頭辞も掃除。
- **データ清掃**: `events/2026-zenkokuken-27.json` books[0] に露出していた編集メモ（「主催／書籍著者としては未確認」等）を削除。両イベントの books の空白のみの `cover`/`amazon_url` を除去。
- **テンプレ導線の補完**: `template/make_template.py` の rooms 色選択肢に濃色 `blueDeep`/`greenDeep` が欠落していたのを、`index.html` の `COLOR` 辞書（6種）に揃えて追加。
- シェル変更のため `sw.js` の `CACHE_VERSION` を v20→v21 に更新。

### 一覧ページの favicon を東洋館出版社サイトに統一
- `index.html` の `<link rel="icon">`/`<link rel="apple-touch-icon">`（静的既定値）を、`www.toyokan.co.jp` と同一の画像（`logo_icon_....jpg`、CDN直接参照）に変更。
- イベントページの `applyAppIdentity()` によるアイコン実行時生成（PWAホーム画面追加用）は影響を受けず従来通り動作（セレクタで `link[rel="icon"]` を取得して上書きするため）。
- `assets/favicon.svg` はコードから参照されなくなったため `sw.js` の `APP_SHELL` プリキャッシュ対象からも除外（ファイル自体は予備として残置）。`CACHE_VERSION` は v21 のまま（未デプロイのため据え置き）。

### オール筑波 算数サマーフェスティバル2026の追加
- Excel入力シート（`イベント情報入力シート_入力済み_2026-math-summer-fes_関連書籍補完.xlsx`）から `events/2026-math-summer-fes.json` を新規生成（eventInfo／sessions 15本／notices 6件／forms／books 14冊）。並行セッションが無いため `rooms: []`。会場マップ画像はシート未指定のため `mapImage` 省略（`mapNote` のみ）。
- `events.json` に1エントリ追記（計3件）。`manifestPath`（実体マニフェスト）は未作成。

### PWA アイコン文字をヘッダー表示と分離可能に（`iconLabel` 追加）
- 従来はホーム画面追加時のアプリ名（ヘッダー表示）とアイコン文字が同一の `logoMain` から派生し、アイコンは `logoMain` 先頭3文字固定だった。「ヘッダーは正式名、アイコンは短い略称にしたい」（例: ヘッダー「算数サマー2026」／アイコン「算サマ」）というニーズに対応するため、`eventInfo.iconLabel`（任意）を新設。
- `index.html` の `applyAppIdentity()` を `info.iconLabel || info.logoMain` でアイコン生成するよう変更（`iconLabel` 未指定時は従来通り `logoMain` 先頭3文字なので既存イベントは無影響）。汎用ロジックのため `template/README.md`／`README.md` にも仕様を追記。
- `events/2026-math-summer-fes.json` に適用（`logoMain`＝「算数サマー2026」、`iconLabel`＝「算サマ」）。シェル変更のため `sw.js` の `CACHE_VERSION` を v22→v23 に更新。

## 残課題 / TODO
- [x] **GitHub Pages の有効化**（Settings → Pages → main / root。CNAME 設置済み・公開中）。
- [ ] **判読困難だった氏名・所属の確認**（画像から転記したもの）:
  - 2日目ワークショップ案内の登壇者・所属（例: 山本良一／島根・雲南市立木次小、髙木美和／福岡・赤村立赤小 など）。
  - シンポジウム討論者「久保田健功」の表記。
  - 修正は `events/2026-zensanken-37.json` の該当箇所のみ。
- [ ] （任意）QRコード生成の仕組み。
- [ ] （任意）書籍データの拡充（実際の販売書籍リスト）。
- [ ] （任意）会場マップ画像（`assets/venue-map-2026-zensanken-37.svg`）の本番図面への差し替え。
- [ ] （任意）PWAアイコン（`assets/icon.svg`）の本番デザインへの差し替え。
