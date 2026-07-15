# 開発の記録（progress.md）

このPWAの開発経緯・現状・残課題のログです。新しい作業を行ったら追記してください。

## 現状サマリ
- **マルチイベント対応のタイムテーブル PWA が完成**し、`main` にマージ済み。
- 公開URL（GitHub Pages 有効化後）:
  - イベント一覧: `https://<user>.github.io/t-pod/`
  - 個別イベント: `https://<user>.github.io/t-pod/?id=2026-zensanken-37`
- 現在登録されているイベント: **第37回 全国算数授業研究大会**（`events/2026-zensanken-37.json`、amber `#f59e0b`）／**第27回 全国国語授業研究大会**（`events/2026-zenkokuken-27.json`、シアン `#00a7d8`）／**オール筑波 算数サマーフェスティバル2026**（`events/2026-math-summer-fes.json`、スカイブルー `#0ea5e9`）の3件。
- 現在のデザイン: ロゴ調のコンパクトなヘッダー（**スクロールで縮小**）、フッターは **TIMETABLE / FILES / BOOKS** の3タブ。テーマ色は `eventInfo.brandColor` で**イベント毎に変更可能**（濃淡は自動生成、**背景色の輝度に応じて文字色 `--brand-fg` を白/濃紺に自動切替**）。**一覧ページの基調色は東洋館イメージカラーのイエロー `#ffd900`**、一覧の各カードは `events[].brandColor` でイベント固有色に切替。
- LINE 友だち追加ポップアップは**イベントはオプトイン（`eventInfo.linePromo: true`）／一覧ページは初回のみ**表示（現行3イベントは LINE 経由アクセスのため非表示）。

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

### デザイン検証と改善（コントラスト自動判定・縮小ヘッダー・LINE導線見直し）
- **背景色に応じた文字色の自動切替（コントラスト事故の解消）**: 一覧ページの基調色 `#ffd900`（純黄色）の上にヘッダー等が白文字で載り、WCAG 大幅未達で判読困難だった。CSS 変数 `--brand-fg` を新設し、ブランド色の sRGB 相対輝度（`relativeLuminance()`）を JS で判定して、明るい色なら濃紺 `#1e293b`・暗い色なら白を自動選択（`updateBrandFg()`、閾値 0.55）。ヘッダー・FAB・日付タブ active・インストールバナー・実行時生成する PWA アイコン文字の固定 `text-white` を `text-brand-fg` に置換。`tailwind.config` の `brand.fg` と `safelist` に追加。どんな `brandColor`（明暗どちらでも）でも文字が読めるようにした。`<meta name="theme-color">` の既定値も `#f59e0b` → `#ffd900` に是正（`--brand` 既定と一致）。
- **スクロール連動の縮小ヘッダー＋質感更新**: 濃いグラデ＋`drop-shadow`＋`shadow-lg` の 2018 年頃風マテリアルを、フラット寄り（`shadow-sm`・グラデ控えめ）に更新。スクロール（>48px）でタイトル縮小＋サブタイトル非表示にコンパクト化し、上端付近（<8px）で復元（閾値を分けてちらつき防止、`transition` は `font-size`/`padding` のみ 150ms、`prefers-reduced-motion` では即時切替）。縦空間を確保。
- **LINE 友だち追加ポップアップの表示条件を再設計**:
  - 従来: イベント初回訪問の 0.9 秒後に全画面表示（コンテンツ閲覧前の割り込みで離脱要因）。
  - 変更後（「閲覧後」表示・1回のみ・`localStorage` 制御）:
    - **イベントページはオプトイン**（`eventInfo.linePromo === true` のときだけ表示）。現行3イベントはすべて LINE 経由でアクセスするため既定の非表示のまま（`linePromo: false`）。新規イベントは `true` を指定すれば表示できる。
    - **一覧ページ（`?id` 無し）は初回訪問時のみ表示**（LINE 以外からの流入もあるため）。縦が短くタブ切替も無いので、スクロール 120px 超または 5 秒経過で表示（イベントは 300px／30秒）。
  - 表示タイミングは「一定スクロール・タブ切替・一定時間経過のいずれか早いタイミング」。モーダル表示中は重ねず閉じてから表示。
- **テンプレート更新**: `template/make_template.py` の基本情報シートに「LINE追加ポップアップ（true/false）」行を追加し `イベント情報入力シート.xlsx` を再生成。`template/README.md` に `linePromo` のオプトイン仕様を追記。
- シェル変更のため `sw.js` の `CACHE_VERSION` を v23→v24→v25 に更新（コントラスト/ヘッダー対応で v24、LINE 導線見直しで v25）。

### ノッチ/ステータスバー色をイベント色に揃える（`theme-color` のパース時反映）
- **課題**: LINE 等のアプリ内ブラウザは `<meta name="theme-color">` を**ページのパース時に一度だけ**読み、JS の事後更新を反映しない。従来 `applyBrandColor()` は JSON 取得後にシアン等へ更新していたが、LINE のバー（ノッチ/ステータスバー部）は静的既定値 `#ffd900`（黄）で固定されたままだった。
- **対応（汎用シェルを維持したまま生成的に解決）**: イベントのブランド色を **localStorage にキャッシュ（キー `t-pod:theme:<id>`）** し、次回訪問時に **head の inline スクリプトがパース時点で `theme-color` へ即時反映**する方式に変更。
  - `applyBrandColor()`: 適用したブランド色を同キーにキャッシュ（次回用）。
  - head inline スクリプト: `?id` に対応するキャッシュ色があればパース時点で `theme-color` メタへ反映。`theme-color` メタを inline スクリプトより前に移動（スクリプトから参照可能に）。
- **既知の制約**: 2 回目以降の訪問は確実に反映。まっさらな端末の**初回訪問のみ**、色を知る前に LINE がバーを読むため一瞬既定の黄になり得る（イベントアプリは LINE から繰り返し開く運用のため実用上ほぼ問題なし）。初回も完全一致させるにはイベント別の実体 HTML か色の静的埋め込みが必要で、「単一汎用シェル」方針とのトレードオフ。
- シェル変更のため `sw.js` の `CACHE_VERSION` を v25→v26 に更新。

### ノッチ色の恒久対策（Service Worker がシェル HTML の theme-color を書き換え）
- **残っていた問題**: 上記の localStorage + JS 方式でも、iOS Safari は**サーバーから受け取った生 HTML の静的 `theme-color`（既定 `#ffd900`）**をパース〜リロード時のオーバースクロール背景に採用し、JS の事後変更の反映が遅れる。結果、**リロード直後にノッチ/上部が黄色へ戻る**現象が残っていた（読み込みスピナー中は特に顕著）。
- **恒久対策**: Service Worker の fetch ハンドラで、**ナビゲーション要求（`request.mode === "navigate"`）を専用処理**（`handleNavigate()`）に分離。`?id` があれば `events/<id>.json` の `eventInfo.brandColor`（`getBrandColor()`、キャッシュ優先→無ければ取得）を並行取得し、シェル HTML 内の `<meta name="theme-color" content="…">` を**イベント色へ書き換えてから返す**。これにより **Safari が受け取る生 HTML の時点で theme-color が正しい色**になり、パース/リロード時も黄へ戻らない。一覧ページ（`?id` 無し）や取得失敗時は素のシェル（既定 `#ffd900`）を返す。
  - 従来の Network First は `networkFirst()` に切り出して共通化。`HEX_RE` で色を検証。
  - **検証**: スクリプト無効（`sandbox="allow-same-origin"`）の iframe で読み込み（＝ページ JS が一切動かない状態）、SW 書き換え結果のみの `theme-color` が 全国研`#00a7d8`／全算研`#f59e0b`／サマー`#0ea5e9`／一覧`#ffd900` と各イベント色に一致することを確認。
  - 効果は SW 制御下（＝2 回目以降、実質すべてのリロード）で有効。SW 未登録の初回ヒットのみ生の既定色。
- シェル変更のため `sw.js` の `CACHE_VERSION` を v26→v27 に更新。

### 初回訪問のノッチ色も揃える（SW 制御取得後の自動リロード）
- **残っていた問題**: 上の SW 書き換えは **SW が制御している場合のみ**有効。新しい端末の**初回アクセス**は SW 未制御のため GitHub Pages の生 HTML（既定 `theme-color`=黄）がそのまま表示され、iOS Safari はそれをパース時に読んでノッチが黄のまま固定される（本番 v27 で実機確認 → 初回は黄のまま、を再現）。
- **対応**: `registerSW()` を変更。**初回訪問（`navigator.serviceWorker.controller` が null）でイベントページを開いたときだけ**、SW が制御を取得した瞬間（`controllerchange`）に **一度だけ `location.reload()`**。リロード後のナビゲーションは SW 制御下で `handleNavigate()` が書き換えた HTML を返すため、ノッチ色が確定する。
  - **ループ防止**: `sessionStorage["t-pod:sw-reload"]` で「セッション内1回のみ」に制限。制御下で開始した2回目以降・一覧ページ・更新時は自動リロードしない（`wasUncontrolled && getEventId()` 条件）。
  - **検証**: SW 全解除＋キャッシュ削除で新端末を再現 → イベントページを開くと自動で1回リロードし、`sessionStorage` フラグが立ち、SW 制御下＋正しい色（全算研 `#f59e0b`）になることを確認。2回目ナビ・手動リロードでは再リロードしない（ループ無し）ことも確認。コンソールエラー無し。
  - **トレードオフ**: 新端末の初回のみ、黄の一瞬 →（〜1秒）自動リロード → イベント色、という遷移になる（LINE/QR から繰り返し開く運用では実用上問題なし）。
- シェル変更のため `sw.js` の `CACHE_VERSION` を v27→v28 に更新。

### 自動リロードを別 URL 置換に変更（iOS Safari の status bar 色キャッシュ対策）
- **問題**: 本番 v28 でも iOS Safari では最上部（status bar/ノッチ帯）が黄のまま。この帯は iOS Safari が `theme-color` で塗る領域で、**同一 URL のリロードでは iOS Safari が status bar の `theme-color` を再読込しない**（初回パース値を保持する）ことが原因と推定。SW 書き換え自体は本番でも有効（Chrome の sandboxed iframe で amber/シアンを確認済み）だが、初回リロード後も iOS がキャッシュした黄を保持していた。
- **対応**: `registerSW()` の自動リロードを、同一 URL の `location.reload()` から**キャッシュバスター付きの別 URL への `location.replace()`**（`?id=… &_r=1`）に変更。別 URL にすることで iOS Safari に確実に再パースさせ、SW 制御下で書き換わった `theme-color`（イベント色）を読ませる。`?id` は保持されるので SW の `handleNavigate()` はそのまま機能。
  - **ループ防止**: URL に `_r` があれば「リロード済み」とみなし再リダイレクトしない（＋従来の `sessionStorage["t-pod:sw-reload"]` ガードも併用）。
  - **検証（Chrome）**: 新端末再現（SW 全解除＋キャッシュ削除）→ イベントページを開くと `?id=…&_r=1` へ自動置換され、SW 制御下＋正しい色（全国研 `#00a7d8`）に。`_r` 付き URL では再リダイレクトせず（`_r` は1個のまま）ループ無し。コンソールエラー無し。
  - **未検証事項（要実機確認）**: iOS Safari が `theme-color` を **URL 単位でキャッシュ**するなら別 URL 化で直る想定。もし **タブ単位でキャッシュ**する挙動なら本対応でも直らず、その場合はイベント別の静的 HTML エントリ（生成物、URL/QR 方針の見直しを伴う）が必要になる。
- シェル変更のため `sw.js` の `CACHE_VERSION` を v28→v29 に更新。
- **結果・現状（2026-07-10 時点）**: v29 をデプロイして iOS Safari 実機で確認したが **ノッチ帯は黄のまま＝反映されず**。「URL 単位キャッシュ」仮説では直らなかったことになり、この件は**いったん保留**とする。
  - **制約（今後の方針）**: **公開済み URL（`?id=<id>`）は変更しない**方針を確定。したがって `&_r=1` を付与する現行 v29 の別 URL 置換は暫定であり、恒久策としては採らない（URL が汚れる／共有・ブックマーク・履歴に残るため）。URL を変えずにノッチ色を合わせる方法を引き続き検討する。
  - **次に検討する案（URL 不変が前提）**: ①`?id=<id>` のまま Service Worker 側で初回ナビゲーションを確実に横取りする（`clients.claim()` のタイミング／`navigationPreload` 等の見直し）。②`&_r=1` を付けず `history.replaceState` で URL を戻しつつ再パースさせる方法の可否検証。③イベント別の静的 HTML を用意しても**公開 URL は `?id=` のまま**にできる配信（例: リダイレクトではなく SW が `?id=` に対してイベント別 HTML を合成して返す）。いずれも iOS 実機での検証が必須。

### URL 不変のノッチ色対策（セーフエリア上端をブランド色で描画）
- **方針転換**: iOS Safari 実機では、`theme-color` を SW で書き換えても同一タブのノッチ/ステータスバー色が黄のまま保持されるケースが残ったため、`theme-color` の再読込に依存しない対策へ変更。
- **対応**:
  - `registerSW()` から `&_r=1` 付き `location.replace()` を撤去。公開済み URL（`?id=<id>`）を汚さない方針に戻した。
  - 画面最上部の `env(safe-area-inset-top)` 領域を `--brand` で塗る固定レイヤー `.safe-area-top-bg` を追加。ヘッダー本体は `max-w-2xl`・角丸のまま、ノッチ帯だけは画面端までイベント色で埋める。
  - `apple-mobile-web-app-status-bar-style` を `black-translucent` に変更し、ホーム画面追加時にも上端の Web コンテンツ色がステータスバー背面に出やすい設定にした。
- **効果の狙い**: iOS が `theme-color` をタブ単位で保持しても、実際に表示されるセーフエリア背景をアプリ側の CSS 変数で制御する。`applyBrandColor()` が `--brand` を更新するため、イベント JSON 読み込み後にノッチ帯も個別研究会ページの色へ揃う。
- シェル変更のため `sw.js` の `CACHE_VERSION` を v29→v30 に更新。
- **結果（2026-07-10、v30 デプロイ後 iOS Safari 実機で確認）**: **解消を確認**。`theme-color` の再読込に依存せず、セーフエリア上端を独自レイヤーで塗る方式に切り替えたことで、個別イベントページを開くとノッチ/ステータスバー帯がそのイベントのブランド色になった。公開済み URL（`?id=<id>`）も変更なし。長らく残っていたノッチ色問題はこれで**解決とする**。

### お知らせの未読バッジ化（1度閲覧すると赤い数字が消える）
- **課題**: ヘッダーのベルの赤いバッジが `notices.length`（総件数）を無条件に表示し続け、既読状態を持っていなかった。一度お知らせを読んでも数字が消えず、常時点灯したバッジは通知としての意味を失っていた。
- **対応（案B: 内容ベースの既読判定）**: 単純な「開いたら以後非表示」ではなく、**未読件数**を表示する方式を採用。会期中に主催者がお知らせを追加・修正しても参加者が見落とさないようにするため。
  - 既読は各お知らせの**署名（`title` + `body`）の配列**を `localStorage["t-pod:notices-read:<イベントid>"]` に保存（イベント毎に独立）。件数ではなく内容で判定するため、お知らせが追加・更新されるとその項目だけが未読に戻り、再びバッジが出る。
  - `renderNoticeBadge()`: 未読 = 保存済み署名に含まれないお知らせ、として件数を算出。0 件ならバッジ自体を非表示（従来は `hidden` を外すだけで、消す経路が無かった）。
  - `openNotices()`: モーダルを開いた直後に `markNoticesRead()` → `renderNoticeBadge()` で即座にバッジへ反映。
  - localStorage が使えない環境（プライベートモード等）は try/catch で握って「全件未読」として振る舞い、表示は壊れない（既存の LINE/インストール導線の localStorage 利用と同じ流儀）。
- **検証**: メインスクリプトの構文チェック（`node --check`）と `git diff` を確認。ブラウザ実機での挙動確認は未実施。
- **付随**: Edit ツールが `index.html`/`sw.js` を CRLF に一括変換してしまったため LF へ復元（差分が全行に及んでいないことを確認済み）。
- シェル変更のため `sw.js` の `CACHE_VERSION` を v33→v34 に更新。

### ボトムナビのピル幅統一＋UI不揃い解消
- **ボトムナビ選択時ピルの幅揃え**: `.navpill` 3箇所（TIMETABLE / FILES / BOOKS）に `w-full max-w-[120px]` を追加。ラベル長がバラバラなため選択するたびに色面の幅が変わっていたのを、3つとも常時 120px で固定。rem 指定では環境次第で字が折り返す恐れがあったため **px 固定**に。
- **選択時の `font-extrabold` トグルを廃止**: 選択時だけ字が太くなり文字幅が微動していたのを防止。強調は `grad-pill`（背景色）+ `shadow-fab` で充分効く。`safelist` の `font-extrabold` は日付タブが使うため**残す**。
- **アイコンタイルの寸法統一**: 追加バナーのアイコン枠 `w-9 h-9 rounded-lg` → `w-10 h-10 rounded-xl`（資料リンクのアイコン枠と同寸に）。
- **バナー角丸の統一**: オフラインバナー・エラーボックスの `rounded-lg` → `rounded-xl`（追加バナーと同じに統一。カード `rounded-2xl` より一段小さく階層は保つ）。
- **検証済み**: 3タブピル幅・高さ一致、切替時にラベル位置が動かない、320px/375px 幅でも 3つ同時に縮小・はみ出しなし。アイコンタイルと角丸も意図通り統一。
- シェル変更のため `sw.js` の `CACHE_VERSION` を v34→v35 に更新。

## 残課題 / TODO

### 2026-07-15 公開連絡先の整理

- `events/2026-zenkokuken-27.json`から電話番号、個人Gmail、担当者名・個人宛メールを削除。
- 問い合わせ先は研究会事務局と東洋館出版社の公式窓口を案内する表現へ統一。
- Tailwind Play CDNを`3.4.17`へ固定し、Service Workerのキャッシュをv33へ更新。

- [x] **GitHub Pages の有効化**（Settings → Pages → main / root。CNAME 設置済み・公開中）。
- [ ] **判読困難だった氏名・所属の確認**（画像から転記したもの）:
  - 2日目ワークショップ案内の登壇者・所属（例: 山本良一／島根・雲南市立木次小、髙木美和／福岡・赤村立赤小 など）。
  - シンポジウム討論者「久保田健功」の表記。
  - 修正は `events/2026-zensanken-37.json` の該当箇所のみ。
- [ ] （任意）QRコード生成の仕組み。
- [ ] （任意）書籍データの拡充（実際の販売書籍リスト）。
- [ ] （任意）会場マップ画像（`assets/venue-map-2026-zensanken-37.svg`）の本番図面への差し替え。
- [ ] （任意）PWAアイコン（`assets/icon.svg`）の本番デザインへの差し替え。
