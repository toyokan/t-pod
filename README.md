# t-pod

教育イベント・研究会向けのタイムテーブル PWA です。参加者はスマートフォンから、プログラム・配布資料・関連書籍を閲覧できます。

## 特徴

- 静的サイト（HTML / Vanilla JS / Tailwind CSS Play CDN）として GitHub Pages で公開
- `?id=<イベントID>` で複数イベントを切り替え
- UI とイベントデータを分離し、新規イベントは JSON の追加だけで運用
- Service Worker の Network First キャッシュによるオフライン対応
- イベント別のブランド色、PWA 名・アイコン（実体 `.webmanifest` 推奨）、会場マップに対応
- TIMETABLE / FILES / BOOKS の3画面と、スマートフォン向けのスワイプ操作
- 当日は該当する日付タブを初期表示し、現在の進行位置へ自動スクロール
- 半透明の固定ヘッダーと、画面下端から浮かせたガラス調のボトムナビ（iOS 26 Liquid Glass 風のカプセル）。短いタブ切替・押下フィードバックなど、軽量なモダンUI（動きを減らす設定・透明度を下げる設定・非力な端末では不透明版へ自動で落とす）
- 右下にドット絵のマスコット「ふせんネコ」。イベントデータと現在時刻から「あと◯日だよ」「いまは◯◯の時間だよ」などを吹き出しで伝える。造形は 24×24 のグリッド定義 1 箇所から実行時生成し、色はイベントのブランド色に追従（`eventInfo.mascot: false` で無効化可）
- ふせんネコは配布用の SVG 資産（標準・にっこり・まじめ・うれしい・ひらめき）としても取り出せる。同じ定義から生成しているので、アプリ内の表示と配布アイコンでシルエットがずれない
- JSON 由来テキスト・URL のサニタイズ、モーダルのフォーカストラップ、通信タイムアウト時の再試行導線など、堅牢性・アクセシビリティに配慮
- 参加者向けページは検索結果に掲載させず、ルートURLから個別イベントの一覧を公開しない

## URL

| URL | 表示 |
| --- | --- |
| `/` | LINEまたはQRコードからのアクセス案内と、東洋館出版社公式LINEの友だち追加ボタン |
| `/?id=2026-zensanken-37` | 指定イベントのプログラム・資料・書籍 |

作成済みイベントの本番URLは、[開発者向けイベントURL台帳](docs/event-url-index.md)で確認できます。

**LINE公式アカウントのキーワード応答に貼るリンクは、台帳の「LINE配信用URL」列（`?id=<id>&openExternalBrowser=1`）を使ってください。** LINEが送ったリンクはそのままだとLINE内ブラウザで開き、そこではAndroidの「ホーム画面に追加」プロンプトが発火せず、iOSの共有シートにも「ホーム画面に追加」が出ません。`openExternalBrowser=1` を付けると端末のChrome / Safariで直接開くため、追加の導線がそのまま機能します。付け忘れてLINE内ブラウザで開かれた場合に備えて、アプリ側にも開き直しの案内（バナー→モーダル）を用意しています。

## 新しいイベントを追加する

1. `events/<id>.json` を作成する。`<id>` は半角英数・ハイフン・アンダースコアのみ。**ルートの `id` フィールドをファイル名と同じ値にする**（既存を複製した場合は書き換え忘れに注意。ファイル名との不一致は `scripts/validate_events.py` がエラー検出）。
2. `events.json` の `events[]` に開発・検証用の索引を1件追加する。

> 似た名称（全国算数／算数サマーフェス）や年度違いの取り違えを避けるため、編集対象は `python scripts/find_event.py "<キーワード>"` で id・ファイルパスを確定してから着手できます（`--current` / `--upcoming` で今日基準の現行イベントも確認可）。
3. イベント別マニフェスト（`events/<id>.webmanifest`）とアイコン、会場マップを追加する。マニフェストは data URI 動的生成にフォールバックできるが、iOS では `scope` の扱いが不安定になり外部リンクから PWA へ戻りにくくなるため、**実体ファイルの用意を推奨**（`eventInfo.manifestPath` で参照）。
4. `/?id=<id>` をローカルで確認し、チラシ等の QR コードに設定する。

### 終了したイベントの扱い

終了後もページは削除せず公開したままにします（旧チラシの QR を生かすため）。終了かどうかは**開催日から自動判定**します。**最終開催日の 1 週間後（＋7日）を過ぎたイベントは「終了済み」**とみなし、個別 JSON を原則更新・複製しません（似た名称・同じ会の別回との取り違え防止）。手動フラグは不要ですが、中止・延期など特殊ケースのみ個別 JSON ルート直下に `"_status": "ended"` / `"active"` を置くと日付判定より優先されます（UI では未使用）。

JSON に不慣れな担当者向けに、[Excel 入力ひな形](template/イベント情報入力シート.xlsx) と [記入・変換手順](template/README.md) を用意しています。
生成後は、イベント索引・開発者向けURL台帳・個別JSON・日付ID・会場ID・マニフェスト・アイコンの整合性を検証します。

```bash
python scripts/import_event_workbook.py "入力済みイベント.xlsx"
python scripts/import_event_workbook.py "入力済みイベント.xlsx" --write
python scripts/validate_events.py --event <id>
```

Excel取込ではURL台帳も自動更新されます。`events.json` を手動編集した場合は、次のコマンドで台帳を更新してください。

```bash
python scripts/generate_event_url_index.py
```

第37回全国算数授業研究大会の「事後アンケート（参加者全員）」と「当日資料一式（PDF）」は、公開URLの確定後に追加する保留項目です。仮URLのまま公開しない運用とします。

## ローカル確認

`file://` では fetch と Service Worker が動かないため、静的サーバを使用します。

```bash
python3 -m http.server 8080
```

- 参加者向け案内: `http://localhost:8080/`
- 個別イベント: `http://localhost:8080/?id=2026-zensanken-37`
- 存在しないイベント: `http://localhost:8080/?id=does-not-exist`

JSON の構文確認例:

```bash
python3 -m json.tool events.json
python3 -m json.tool events/2026-zensanken-37.json
```

### 検証（CI と同じコマンド）

プルリクエストと `main` への push では、GitHub Actions が次の 2 つを実行します（`.github/workflows/validate-events.yml`）。手元でも同じコマンドで確認できます。

```bash
python -m pip install -r requirements-tools.txt
python scripts/validate_events.py                 # イベントJSON・索引・アセットの整合性
python -m unittest discover -s tests -v           # 回帰テスト
```

`tests/` が見ているのは、イベント関連スクリプトの挙動（`test_event_tools.py`）、ふせんネコの造形と生成物のずれ（`test_fuseneko.py`）、そして UI シェルのソースそのもの（`test_shell_source.py`）です。最後のひとつは `index.html` に NUL バイトが混ざっていないことを確かめます——HTML パーサーは NUL を U+FFFD へ黙って置き換えてしまい、`grep` や `diff` もこのファイルを「バイナリ」として扱うようになるためです。

### マスコット「ふせんネコ」

造形の定義は `assets/fuseneko/fuseneko-grid.js` の 1 箇所だけです。配布用の SVG
（`assets/fuseneko/fuseneko-*.svg`）はそこから生成するため、**手では編集しません**。

```bash
python3 scripts/build_fuseneko.py            # SVG を生成する
python3 scripts/build_fuseneko.py --check    # 生成物が定義とずれていないか調べる
python3 scripts/build_fuseneko.py --preview  # ターミナルにドット絵を描く
python3 scripts/build_fuseneko.py --preview FN_HAPPY   # 表情を重ねて描く
```

サイズ・表情・色・背景を並べた確認ページ: `http://localhost:8080/dev/fuseneko.html`

**隠し要素**（いずれもイベントページのみ）:

| 操作 | 起こること |
| --- | --- |
| 右下のネコを**素早く 3 回つつく** | 「ぼく、ふせんネコ！」と名乗る |
| 右下のネコを**長押し**（0.6 秒以上） | 「ごろごろ…」となでられて、ハートが出る |
| **深夜（0〜5 時）・早朝（5〜7 時）に開く** | その時間だけの一言が増える |

名乗った文言は 8 秒ほどでいつもの一言に戻ります。名前はボタンの読み上げ／ホバー表示にも
入っているので、支援技術やパソコンからも分かります。

ページに埋め込むときは `fuseneko-grid.js` → `fuseneko.js` の順に読み込み、
`createFuseneko({ size, color, expression, ariaLabel })` を呼びます。
色は 1 色（テーマ色）だけ渡せば、本体・折り返し・輪郭・目鼻口の濃淡が自動で決まります。

## ドキュメント

- [要件・データ仕様・運用ルール](docs/requirements.md)
- [開発者向けイベントURL台帳](docs/event-url-index.md)
- [開発経緯・現状・残課題](progress.md)
- [Excel 入力ひな形の記入・変換手順](template/README.md)
- [イベントJSON Schema](template/event-data.schema.json)
- [新規イベント登録フローの見直し記録](docs/event-onboarding-review.md)
- [公開範囲の検討記録](docs/repository-visibility-review.md)
- [Codex 向け作業ガイド](AGENTS.md)
- [iPhone から Codex クラウドタスクを使う](docs/codex-cloud-setup.md)
- [Claude の定期実行（Routine）設定メモ](docs/claude-routines.md)

詳細仕様は README から `docs/requirements.md` へ分離しています。なお、リポジトリが public の場合は同ファイルも公開されます。

## デプロイ

GitHub の **Settings → Pages** で Source を `Deploy from a branch`、Branch を `main` / `/ (root)` に設定します。パスは相対指定のためサブパス配信にも対応します。

## License

[LICENSE](LICENSE) を参照してください。
