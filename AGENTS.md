# AGENTS.md

このリポジトリで作業するエージェント（Codex・Claude Code 共通）向けのガイドです。`CLAUDE.md` はこのファイルを取り込むだけなので、共通の規則はここに書きます。
詳しい運用手順は `README.md`、これまでの経緯は `progress.md`。ここでは**設計の要点と禁止事項**に絞り、領域ごとの詳しい決めごとと実測の根拠は `docs/architecture/` に置きます。

## プロジェクト概要
- 教育イベント・研究会向けの **タイムテーブル PWA**（静的サイト / GitHub Pages 公開）。
- 参加者がスマホで **プログラム・配布資料・関連書籍** を閲覧できる。
- 技術: HTML5 + Vanilla JS + Tailwind CSS（Play CDN）。ビルド工程なし。

## アーキテクチャの要点
- **JSON駆動・UIとデータ完全分離**。`index.html` は**汎用シェル**で、固有のイベント文言を持たない（タイトル等は JSON から動的反映）。
- **マルチイベント方式（クエリパラメータ）**:
  - `?id=<id>` あり → `events/<id>.json` を fetch して個別イベント表示（イベントモード）。
  - `?id` なし（ルートURL）→ LINE または QR コードからのアクセスを促す静的な案内を表示（コード上は「一覧モード」。`renderAccessGuide()`）。イベント一覧は公開画面に出さない。
  - `index.html` の `getEventId()` が `?id` を取得し `[A-Za-z0-9_-]` のみ許可（不正値・パストラバーサル除去）。`init()` が両モードを分岐。
- **キャッシュと起動経路**: `sw.js` は経路ごとに戦略を変え（`routeOf()`）、`init()` はキャッシュから即描画して裏で取り直す。**`sw.js`・`init()` まわりを触る前に `docs/architecture/cache-and-startup.md` を読む**。必ず守ること:
  - シェル（HTML/JS/アセット）を変更したら **`CACHE_VERSION` を必ず上げる**。
  - **`RUNTIME_CACHE` の名前は `sw.js` と `index.html` の 2 箇所にある**ので必ず揃える。
  - **鮮度の責任は 1 層だけが持つ**（SW はタイムアウトでイベント JSON のキャッシュを返さない）。
  - 静かな再描画は `renderAll({ keepView: true })`。見た目の状態は「出す」「消す」の両方向を書く。
- **見た目と転送量**: **色・フォント・ボトムナビ・アニメーション・画像を触る前に `docs/architecture/ui-style.md` を読む**。必ず守ること:
  - イベント毎のブランド色は `events/<id>.json` の `eventInfo.brandColor` で指定（`applyBrandColor()` が `--brand` を上書き）。
  - **ブランド色ベタ塗り＋白文字を新規に増やさない**。新しい配色は既定の黄 `#ffd900` と amber `#f59e0b` の両方で 4.5:1 以上を実測する。
  - 本文フォントのウェイトは 400/500/700/900 の 4 種から増やさない。
  - アニメーションは `transform` / `opacity` のみ。タッチ／スクロール系リスナの `{ passive: true }` を崩さない。新しい演出は `prefers-reduced-motion` ブロックへ追記する。
  - 告知バナーを原寸のままリポジトリに置かない（`scripts/optimize_images.py`）。書影は `coverUrl()` を通す。新しい `<img>` には `loading="lazy"` と箱の確保を付ける。
- **アイコン**: 絵文字は使わず **SVG（Lucide系）**。`ICONS` レジストリ + `icon(name, cls)` ヘルパ（`index.html`）。静的箇所（ボトムナビ・FAB・モーダル閉じる）はインラインSVG。
- **マスコット（右下のふせんネコ）**: 造形の定義は `assets/fuseneko/fuseneko-grid.js` の 1 箇所だけ。配布用 SVG は生成物で手で編集しない。**マスコットを触る前に `docs/architecture/fuseneko.md` を読む**。
- **PWA アイデンティティ**: `applyAppIdentity()` がイベント毎のアプリ名・アイコン・マニフェストを実行時に差し替える。主要な流入は LINE の in-app ブラウザ。**マニフェスト・favicon・ホーム画面追加の導線を触る前に `docs/architecture/pwa-identity.md` を読む**。
- **描画の安全性**: 文字列は必ず `escapeHtml()`（`index.html`）を通して DOM に入れる。
- **DOM 生成ヘルパ**: `el(tag, class, html)` と `$(id)`（= `getElementById`）を再利用する。

## ファイルマップ
| ファイル | 役割 | 編集方針 |
| --- | --- | --- |
| `index.html` | 汎用 UI シェル + 描画ロジック | ⚠️ ロジック変更時のみ。**固有文言は書かない** |
| `events.json` | イベント索引（スクリプト・URL台帳生成用。UI の一覧表示には未使用。`siteUrl` が本番URL基準） | ✅ イベント追加時に1エントリ追記 |
| `docs/event-url-index.md` | 開発者向け本番URL台帳 | 自動生成（直接編集しない） |
| `events/<id>.json` | 各イベントの全情報（`eventInfo`/`rooms`/`sessions`/`books`） | ✅ ここを追加・編集 |
| `sw.js` | Service Worker | ⚠️ 変更時は `CACHE_VERSION` を上げる |
| `manifest.json` | PWA 汎用シェル（インストール名・色） | △ 任意 |
| `_config.yml` | GitHub Pages（Jekyll）の `exclude`。開発用の文書・スクリプトを公開サイトへ出さない | ⚠️ 開発用のファイル・ディレクトリを足したら追記（`tests/test_shell_source.py` が検査） |
| `assets/` | アイコン・会場マップ（SVG） | △ 任意 |
| `assets/fuseneko/fuseneko-grid.js` | ふせんネコの造形（**唯一の定義**） | ⚠️ 造形を変えるときだけ。SVG 資産の再生成が要る |
| `assets/fuseneko/fuseneko-*.svg` | 配布用 SVG（生成物） | ⛔ 手で編集しない。`python3 scripts/build_fuseneko.py` で作る |
| `assets/fuseneko/fuseneko.js` / `variants.js` | `createFuseneko()` とバリエーション表 | △ 色・表情を足すとき |
| `dev/fuseneko.html` | ふせんネコの確認ページ | △ 任意 |
| `dev/nav-glass.html` | ボトムナビ（Liquid Glass）の確認ページ。Tailwind CDN 無しで動くよう該当ユーティリティを手写ししてある。`?brand=%23f59e0b` でブランド色を差し替え | △ ナビの見た目を変えたら CSS を写し直す |
| `dev/now-card.html` | 進行中カードの演出（回る縁・ドットの波）の確認ページ。ブランド色は画面上のボタンか `?brand=%23005860` で切り替え | △ 進行中カードの CSS を変えたら写し直す |
| `docs/architecture/` | 領域ごとの設計の決めごとと実測の根拠 | 決めごとを変えたら該当ファイルも直す |

## 対象イベントの特定（編集前チェック・重要）
似た名称・年度違いのイベントが並存する（例: 「算数」は `2026-zensanken-37`＝全国算数と `2026-math-summer-fes`＝算数サマーフェスの**両方**に該当。「算数」と「国語」は別会。同じ会は `-<回数>` と `sortDate` の年で年度を識別）。**別イベント・別年度の JSON を誤編集しないため、編集着手前に必ず対象を確定する。**
1. `python scripts/find_event.py "<キーワード>"` で id を確定する（曖昧なら候補と警告が出て exit 2。`--current`/`--upcoming` で今日基準の現行イベントも確認可）。events.json / `docs/event-url-index.md` を直接見てもよい。
2. 編集着手前に **id・title・dateRange・年度** を events.json と照合し、対象を一言で宣言してから編集する。
3. 開いた個別 JSON の**ルート `id` がファイル名と一致**することを確認する（自己識別フィールド。不一致は取り違え・複製書き換え忘れのサイン。`validate_events.py` が ERROR 検出）。
4. 終了済み（最終開催日＋7日超）は原則編集しない（「終了済みイベントの扱い」参照）。

## 新しいイベントの追加手順（コードは触らない）
**推奨**: v2 Excel へ入力・目視修正後、`python scripts/import_event_workbook.py "<xlsx>"` で事前検証し、成功後に `--write` を付けて決定的変換する。既存 ID は上書きしない。新形式は `docs/event-onboarding-review.md` の台帳へ記録する。

手動で追加する場合:

1. `events/<新id>.json` を作成（既存を複製して中身を書き換え／企画書テキストから生成）。`<新id>` は半角英数・ハイフン・アンダースコアのみ。**複製時はルートの `id` を必ず新 id に書き換える**（ファイル名・`events.json` の id と一致必須。ズレは `scripts/validate_events.py` が ERROR で検出）。
   **`rooms[].id` は会場チップにそのまま表示される**（`name` は出ない）ので、`gym`・`r1-1` のような内部コードではなく参加者に見せる表記（例: `1階・6-1教室`／`体育館`）にする。内部コードは `validate_events.py` が WARN で知らせる。
2. `events.json` の `events[]` に1エントリ追記（`id` / `title` / `theme` / `dateRange` / `venueName` / `sortDate`）。手動追加時は `python scripts/generate_event_url_index.py` でURL台帳を更新する（Excel取込時は自動）。
3. **会場マップ（イベント別・任意）**: `eventInfo.venue.mapImage` で指定。会場はイベント毎に異なるため以下を使い分ける。
   - リポジトリ内の図: `assets/venue-map-<id>.svg`（または `.png` / `.jpg`）として置き、`mapImage` に相対パス指定（アイコンの `icon-<id>.svg` と同じイベント別命名で統一）。
   - 外部リンク: 会場図の写真等は `mapImage` に公開URL（Google Drive 等）を直接指定でも可。
   - マップ不要なイベントは `mapImage` を省略（`mapNote` テキストのみ表示、取得失敗時も画像だけ非表示で崩れない）。
4. チラシの QR に `?id=<新id>` を設定。

## ローカル確認
`file://` 直開きは不可（fetch / Service Worker が動かない）。静的サーバを使う。
```bash
python3 -m http.server 8080
# /                         → 参加者向け案内
# /?id=2026-zensanken-37    → 個別イベント
# /?id=does-not-exist       → エラー＋一覧への導線
python3 -m json.tool events.json            # JSON 妥当性チェック
python3 -m json.tool events/2026-zensanken-37.json
```

## 実装後の確認（ローカル・クラウド共通）
- クラウド環境（Codex cloud / Claude Code on the web）の Setup script は `bash scripts/setup_codex_cloud.sh`。
- イベント JSON を編集すると、フック（`.claude/hooks/` / `.codex/hooks/` の `validate_events_on_edit.py`）が `validate_events.py` を走らせ、問題があるときだけ結果を返す。
- 実装後は最低限、次を実行する。

```bash
python scripts/validate_events.py
python -m unittest discover -s tests -v
git diff --check
```

## デプロイ
GitHub **Settings → Pages → Source: `main` / `/ (root)`** → `https://<user>.github.io/t-pod/`。
パスはすべて相対指定のため、サブパス配信（`/t-pod/`）でも追加設定は不要。

## 終了済みイベントの扱い（重要）
- 終了後もページは**削除せず公開状態を維持**する（旧チラシの QR を生かすため）。
- **終了判定は日付から自動**（フラグの手動付与は不要）: **最終開催日 + 7 日 < 今日** なら「終了済み」。最終開催日 = 個別 JSON `eventInfo.dates[]` の最終 `date`（無ければ `events.json` の `sortDate`）。例: 最終日 7/19 → 7/26 まで現行、7/27 以降が終了（当日運用・延長・事後資料追加の猶予）。
- **終了済みの `events/<id>.json` は原則更新・複製しない**。編集・生成の対象は上記判定で現行イベントに限定し、「似た名称・同じ会の別回」との取り違えを避ける。
- 特殊ケース（中止・延期・恒久保留など）のみ個別 JSON ルート直下に `"_status": "ended"` / `"active"` を置いて手動固定する（日付判定より優先。`scripts/find_event.py` と UI のマスコット場面判定 `mascotState()` だけが参照）。

## 禁止 / 注意事項
- **過去の `events/<id>.json` と `events.json` の索引を削除しない**（旧チラシの QR リンクと、`events.json` から生成する開発者向けURL台帳を維持する）。
- `index.html` に特定イベントの固有文言を書かない（汎用シェルを維持）。
- 配布資料の実ファイル（PDF/Word 等）はリポジトリに置かず、外部公開リンク（Google Drive 等）を JSON に記述する。
- フォーム類は PWA 内処理せず外部（Google フォーム等）へ誘導。
- コミットメッセージ・PR・コード・コメント等に **モデル識別子（`gpt-*`・`claude-*` 等）を含めない**。
