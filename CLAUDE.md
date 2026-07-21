# CLAUDE.md

このリポジトリで作業する Claude Code 向けのガイドです。詳しい運用手順は `README.md`、
これまでの経緯は `progress.md` を参照してください。ここでは**設計の要点と禁止事項**に絞ります。

## プロジェクト概要
- 教育イベント・研究会向けの **タイムテーブル PWA**（静的サイト / GitHub Pages 公開）。
- 参加者がスマホで **プログラム・配布資料・関連書籍** を閲覧できる。
- 技術: HTML5 + Vanilla JS + Tailwind CSS（Play CDN）。ビルド工程なし。

## アーキテクチャの要点
- **JSON駆動・UIとデータ完全分離**。`index.html` は**汎用シェル**で、固有のイベント文言を持たない（タイトル等は JSON から動的反映）。
- **マルチイベント方式（クエリパラメータ）**:
  - `?id=<id>` あり → `events/<id>.json` を fetch して個別イベント表示（イベントモード）。
  - `?id` なし（ルートURL）→ `events.json` を fetch してイベント一覧を表示（一覧モード）。
  - `index.html` の `getEventId()` が `?id` を取得し `[A-Za-z0-9_-]` のみ許可（不正値・パストラバーサル除去）。`init()` が両モードを分岐。
- **キャッシュ**: `sw.js` は **Network First**（取得成功でキャッシュ更新、失敗時はキャッシュ）。
  - シェル（HTML/JS/アセット）を変更したら **`CACHE_VERSION` を必ず上げる**。
  - 個別 `events/<id>.json` は Network First でオンデマンドにキャッシュ → 閲覧済みイベントはオフラインでも表示。
- **スタイル**: Tailwind Play CDN。アクセント色は `tailwind.config` の `theme.extend.colors.brand`。基準色は CSS 変数 `--brand`（既定 amber、`<style>` の `:root` で定義）で、`brand-50〜800` は `color-mix()` により自動生成。**イベント毎のブランド色は `events/<id>.json` の `eventInfo.brandColor`（メイン1色の16進）で指定** → `applyBrandColor()` が実行時に `--brand` を上書き（濃淡は自動）。会場/ルームのテーマ色は `index.html` の `COLOR` 辞書（`chip`/`dot`/`border`）が `tailwind.config` の `venue.*` パレット（blue/green/violet/coral）を参照。rooms の色キー `blue/green/orange/purple` を `venue-blue/green/coral/violet` にマッピング。動的生成するクラスは `tailwind.config` の `safelist` に保持（新色は両方に追加）。
- **コントラストの制約**: `brandColor` は明るい色（amber・黄）も指定されるため、**ブランド色ベタ塗り＋白文字（`--brand-fg`）を新規に増やさない**（実測 1.5〜4.4:1 で WCAG AA 未達。`updateBrandFg()` の輝度閾値 0.55 は緩く、amber でも「白」を選ぶ）。強調は**白ピル（淡地）＋ブランド濃色文字**で行い、濃色は **`color-mix(in srgb, var(--brand) 48%, black)`（＝`brand-800` 相当）**を使う（ボトムナビ・日付タブの実装を参照）。**`brand-700`（62%）は使わない**——既定の黄 `#ffd900` では白地に対し 3.45:1 で AA 未達（`brand-800` なら 5.5:1）。また、**明るいブランド色は淡地（`brand-50`〜`200`）や枠線が白い地から見分けられない**（1.0〜1.7:1）ため、ピルを浮かせるには**グレーのトラック（`bg-slate-200/60`）＋白ピル**が要る。新しい配色を足すときは、既定の黄 `#ffd900` と amber `#f59e0b` の両方で 4.5:1 以上を実測して確認する（`color-mix` の計算結果は Chrome が `oklab()` 表記で返すことがあるため、canvas に塗って RGB を取るのが確実）。
- **アニメーション**: 追加してよいのは `transform` / `opacity` のみ（GPU 合成・ビルド工程なしを維持）。タッチ／スクロール系のリスナは **`{ passive: true }` を崩さない**（スワイプは指追従せず「離した時点でコミット」する設計。`index.html` の `TAB_ORDER` とスワイプ IIFE を参照）。新規の演出クラスは `prefers-reduced-motion` ブロックへ必ず追記する（Tailwind の `transition` / `active:scale-*` はこのブロックの対象外なので取りこぼしに注意）。
- **アイコン**: 絵文字は使わず **SVG（Lucide系）**。`ICONS` レジストリ + `icon(name, cls)` ヘルパ（`index.html`）。静的箇所（ボトムナビ・FAB・モーダル閉じる）はインラインSVG。
- **PWA アイデンティティ（イベント毎・実行時生成）**: `applyAppIdentity()`（`index.html`）が、アプリ名＝`logoMain`（例: 全算研2026）、アイコン＝`brandColor` 地＋`logoMain` の先頭3文字（例: 全算研）を実行時生成し、`apple-touch-icon`（canvas で PNG 化）・`apple-mobile-web-app-title`・`document.title` を差し替える。**マニフェストは `eventInfo.manifestPath`（`events/<id>.webmanifest` 実体ファイル）があればそれを参照（最も確実・iOS でも安定）**。無ければ data URI で動的生成（`start_url`/`scope` は絶対 URL 化必須——相対だと data URI 上で無効になりブラウザが静的 `manifest.json` にフォールバックしてアプリ名が「タイムテーブル」になる）。`logoMain` 未指定イベントは静的 `manifest.json`/`assets/icon.svg` にフォールバック。ホーム画面追加の導線は `setupInstallPrompt()`（Android=`beforeinstallprompt`、iOS=`openModal()` で手順案内）。
- **描画の安全性**: 文字列は必ず `escapeHtml()`（`index.html`）を通して DOM に入れる。
- **DOM 生成ヘルパ**: `el(tag, class, html)` と `$(id)`（= `getElementById`）を再利用する。

## ファイルマップ
| ファイル | 役割 | 編集方針 |
| --- | --- | --- |
| `index.html` | 汎用 UI シェル + 描画ロジック | ⚠️ ロジック変更時のみ。**固有文言は書かない** |
| `events.json` | イベント一覧インデックス（一覧ページの元データ） | ✅ イベント追加時に1エントリ追記 |
| `events/<id>.json` | 各イベントの全情報（`eventInfo`/`rooms`/`sessions`/`books`） | ✅ ここを追加・編集 |
| `sw.js` | Service Worker（Network First） | ⚠️ 変更時は `CACHE_VERSION` を上げる |
| `manifest.json` | PWA 汎用シェル（インストール名・色） | △ 任意 |
| `assets/` | アイコン・会場マップ（SVG） | △ 任意 |

## 対象イベントの特定（編集前チェック・重要）
似た名称・年度違いのイベントが並存する（例: 「算数」は `2026-zensanken-37`＝全国算数と `2026-math-summer-fes`＝算数サマーフェスの**両方**に該当。「算数」と「国語」は別会。同じ会は `-<回数>` と `sortDate` の年で年度を識別）。**別イベント・別年度の JSON を誤編集しないため、編集着手前に必ず対象を確定する。**
1. `python scripts/find_event.py "<キーワード>"` で id を確定する（曖昧なら候補と警告が出て exit 2。`--current`/`--upcoming` で今日基準の現行イベントも確認可）。events.json / `docs/event-url-index.md` を直接見てもよい。
2. 編集着手前に **id・title・dateRange・年度** を events.json と照合し、対象を一言で宣言してから編集する。
3. 開いた個別 JSON の**ルート `id` がファイル名と一致**することを確認する（自己識別フィールド。不一致は取り違え・複製書き換え忘れのサイン）。
4. 終了済み（最終開催日＋7日超）は原則編集しない（「終了済みイベントの扱い」参照）。

## 新しいイベントの追加手順（コードは触らない）
1. `events/<新id>.json` を作成（既存を複製して中身を書き換え／企画書テキストから生成）。`<新id>` は半角英数・ハイフン・アンダースコアのみ。**複製時はルートの `id` を必ず新 id に書き換える**（`events/<id>.json` のファイル名・`events.json` の id と一致必須。ズレは `scripts/validate_events.py` が ERROR で検出）。
2. `events.json` の `events[]` に1エントリ追記（`id` / `title` / `theme` / `dateRange` / `venueName` / `sortDate`）。
3. **会場マップ（イベント別・任意）**: `eventInfo.venue.mapImage` で指定。会場はイベント毎に異なるため以下を使い分ける。
   - リポジトリ内の図: `assets/venue-map-<id>.svg`（または `.png` / `.jpg`）として置き、`mapImage` に相対パス指定（アイコンの `icon-<id>.svg` と同じイベント別命名で統一）。
   - 外部リンク: 会場図の写真等は `mapImage` に公開URL（Google Drive 等）を直接指定でも可。
   - マップ不要なイベントは `mapImage` を省略（`mapNote` テキストのみ表示、取得失敗時も画像だけ非表示で崩れない）。
4. チラシの QR に `?id=<新id>` を設定。

## ローカル確認
`file://` 直開きは不可（fetch / Service Worker が動かない）。静的サーバを使う。
```bash
python3 -m http.server 8080
# /                         → イベント一覧
# /?id=2026-zensanken-37    → 個別イベント
# /?id=does-not-exist       → エラー＋一覧への導線
python3 -m json.tool events.json            # JSON 妥当性チェック
python3 -m json.tool events/2026-zensanken-37.json
```

## デプロイ
GitHub **Settings → Pages → Source: `main` / `/ (root)`** → `https://<user>.github.io/t-pod/`。
パスはすべて相対指定のため、サブパス配信（`/t-pod/`）でも追加設定は不要。

## 終了済みイベントの扱い（重要）
- 終了後もページは**削除せず公開状態を維持**する（旧チラシの QR を生かすため）。
- **終了判定は日付から自動**（フラグの手動付与は不要）:
  - **最終開催日 + 7 日 < 今日** なら「終了済み」とみなす。
  - 最終開催日 = 個別 JSON `eventInfo.dates[]` の最終 `date`（無ければ `events.json` の `sortDate`）。
  - 例: 最終日 7/19 のイベントは **7/26 まで現行扱い**、7/27 以降が終了扱い（当日運用・延長・事後資料追加の猶予）。
- **終了済みイベントの `events/<id>.json` は原則更新しない**。修正・追記・複製元にしない。編集・生成の対象を探すときは、上記判定で終了済みを除外し、現行イベントのみを見る（**「似た名称・同じ会の別回」との取り違え防止**）。
- 例外的に手動で状態を固定したい場合のみ、個別 JSON ルート直下に `"_status": "ended"` または `"active"` を置く（あれば日付判定より優先。中止・延期・恒久保留などの特殊ケース用）。UI では未使用（不明フィールドは無視）。

## 禁止 / 注意事項
- **過去の `events/<id>.json` を削除しない**（旧チラシの QR リンクが無効になる）。一覧から外すだけなら `events.json` のエントリ削除で OK。
- `index.html` に特定イベントの固有文言を書かない（汎用シェルを維持）。
- 配布資料の実ファイル（PDF/Word 等）はリポジトリに置かず、外部公開リンク（Google Drive 等）を JSON に記述する。
- フォーム類は PWA 内処理せず外部（Google フォーム等）へ誘導。
- コミットメッセージ・PR・コード・コメント等に **モデル識別子（`claude-opus-4-8` 等）を含めない**。
