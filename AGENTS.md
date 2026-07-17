# AGENTS.md

このリポジトリで作業する Codex 向けのガイドです。詳しい運用手順は `README.md`、
これまでの経緯は `progress.md` を参照してください。ここでは**設計の要点と禁止事項**に絞ります。

## プロジェクト概要
- 教育イベント・研究会向けの **タイムテーブル PWA**（静的サイト / GitHub Pages 公開）。
- 参加者がスマホで **プログラム・配布資料・関連書籍** を閲覧できる。
- 技術: HTML5 + Vanilla JS + Tailwind CSS（Play CDN）。ビルド工程なし。

## アーキテクチャの要点
- **JSON駆動・UIとデータ完全分離**。`index.html` は**汎用シェル**で、固有のイベント文言を持たない（タイトル等は JSON から動的反映）。
- **マルチイベント方式（クエリパラメータ）**:
  - `?id=<id>` あり → `events/<id>.json` を fetch して個別イベント表示（イベントモード）。
  - `?id` なし（ルートURL）→ LINEまたはQRコードからのアクセスを促す案内を表示（案内モード）。イベント一覧は公開画面に出さない。
  - `index.html` の `getEventId()` が `?id` を取得し `[A-Za-z0-9_-]` のみ許可（不正値・パストラバーサル除去）。`init()` が両モードを分岐。
- **キャッシュ**: `sw.js` は **Network First**（取得成功でキャッシュ更新、失敗時はキャッシュ）。
  - シェル（HTML/JS/アセット）を変更したら **`CACHE_VERSION` を必ず上げる**。
  - 個別 `events/<id>.json` は Network First でオンデマンドにキャッシュ → 閲覧済みイベントはオフラインでも表示。
- **スタイル**: Tailwind Play CDN。アクセント色は `tailwind.config` の `theme.extend.colors.brand`。基準色は CSS 変数 `--brand`（既定 amber、`<style>` の `:root` で定義）で、`brand-50〜800` は `color-mix()` により自動生成。**イベント毎のブランド色は `events/<id>.json` の `eventInfo.brandColor`（メイン1色の16進）で指定** → `applyBrandColor()` が実行時に `--brand` を上書き（濃淡は自動）。会場/ルームのテーマ色は `index.html` の `COLOR` 辞書（`chip`/`dot`/`border`）が `tailwind.config` の `venue.*` パレット（blue/green/violet/coral）を参照。rooms の色キー `blue/green/orange/purple` を `venue-blue/green/coral/violet` にマッピング。動的生成するクラスは `tailwind.config` の `safelist` に保持（新色は両方に追加）。
- **アイコン**: 絵文字は使わず **SVG（Lucide系）**。`ICONS` レジストリ + `icon(name, cls)` ヘルパ（`index.html`）。静的箇所（ボトムナビ・FAB・モーダル閉じる）はインラインSVG。
- **PWA アイデンティティ（イベント毎・実行時生成）**: `applyAppIdentity()`（`index.html`）が、アプリ名＝`logoMain`（例: 全算研2026）、アイコン＝`brandColor` 地＋`logoMain` の先頭3文字（例: 全算研）を実行時生成し、`apple-touch-icon`（canvas で PNG 化）・`apple-mobile-web-app-title`・`document.title` を差し替える。**マニフェストは `eventInfo.manifestPath`（`events/<id>.webmanifest` 実体ファイル）があればそれを参照（最も確実・iOS でも安定）**。無ければ data URI で動的生成（`start_url`/`scope` は絶対 URL 化必須——相対だと data URI 上で無効になりブラウザが静的 `manifest.json` にフォールバックしてアプリ名が「タイムテーブル」になる）。`logoMain` 未指定イベントは静的 `manifest.json`/`assets/icon.svg` にフォールバック。ホーム画面追加の導線は `setupInstallPrompt()`（Android=`beforeinstallprompt`、iOS=`openModal()` で手順案内）。
- **描画の安全性**: 文字列は必ず `escapeHtml()`（`index.html`）を通して DOM に入れる。
- **DOM 生成ヘルパ**: `el(tag, class, html)` と `$(id)`（= `getElementById`）を再利用する。

## ファイルマップ
| ファイル | 役割 | 編集方針 |
| --- | --- | --- |
| `index.html` | 汎用 UI シェル + 描画ロジック | ⚠️ ロジック変更時のみ。**固有文言は書かない** |
| `events.json` | 開発・検証・URL台帳生成用のイベント索引（`siteUrl` が本番URL基準） | ✅ イベント追加時に1エントリ追記 |
| `docs/event-url-index.md` | 開発者向け本番URL台帳 | 自動生成（直接編集しない） |
| `events/<id>.json` | 各イベントの全情報（`eventInfo`/`rooms`/`sessions`/`books`） | ✅ ここを追加・編集 |
| `sw.js` | Service Worker（Network First） | ⚠️ 変更時は `CACHE_VERSION` を上げる |
| `manifest.json` | PWA 汎用シェル（インストール名・色） | △ 任意 |
| `assets/` | アイコン・会場マップ（SVG） | △ 任意 |

## 新しいイベントの追加手順（コードは触らない）
**推奨**: v2 Excelへ入力・目視修正後、`python scripts/import_event_workbook.py "<xlsx>"` で事前検証し、成功後に `--write` を付けて決定的変換する。既存IDは上書きしない。新形式は `docs/event-onboarding-review.md` の台帳へ記録する。

手動で追加する場合:

1. `events/<新id>.json` を作成（既存を複製して中身を書き換え／企画書テキストから生成）。`<新id>` は半角英数・ハイフン・アンダースコアのみ。
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

## デプロイ
GitHub **Settings → Pages → Source: `main` / `/ (root)`** → `https://<user>.github.io/t-pod/`。
パスはすべて相対指定のため、サブパス配信（`/t-pod/`）でも追加設定は不要。

## 禁止 / 注意事項
- **過去の `events/<id>.json` と `events.json` の索引を削除しない**（旧チラシのQRリンクと開発者向けURL台帳を維持する）。
- `index.html` に特定イベントの固有文言を書かない（汎用シェルを維持）。
- 配布資料の実ファイル（PDF/Word 等）はリポジトリに置かず、外部公開リンク（Google Drive 等）を JSON に記述する。
- フォーム類は PWA 内処理せず外部（Google フォーム等）へ誘導。
- コミットメッセージ・PR・コード・コメント等に **モデル識別子（`Codex-opus-4-8` 等）を含めない**。
