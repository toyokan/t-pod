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
  - `?id` なし（ルートURL）→ 静的な参加者向け案内ページを表示（一覧モード。`renderAccessGuide()`）。`events.json` はイベント一覧の表示には使われず、`scripts/` や `docs/event-url-index.md` 生成用のインデックスとしてのみ参照される。
  - `index.html` の `getEventId()` が `?id` を取得し `[A-Za-z0-9_-]` のみ許可（不正値・パストラバーサル除去）。`init()` が両モードを分岐。
- **キャッシュ（`sw.js`）**: 会場の回線は「切れている」より**「つながっているが極端に遅い」**ことのほうが多く、
  素の Network First はこの状態がいちばん苦手（手元にキャッシュがあってもネットワークを待ち続ける）。
  そこで**経路ごとに戦略を変える**（`routeOf()`）。
  - `immutable`（`cdn.tailwindcss.com` / `fonts.googleapis.com` / `fonts.gstatic.com`）＝**キャッシュ優先・再検証なし**。
    版が URL に入っていて内容が変わらないので安全。2 回目以降は通信ゼロになる。
  - `passthrough`（その他クロスオリジン＝書影）＝**SW を通さない**。ブラウザの HTTP キャッシュに任せたほうが速く、
    SW のキャッシュを画像で埋めずに済む。
  - `eventJson`（`events/<id>.json`）＝ネットワーク優先。**会場のキャプティブポータルは JSON の URL にも
    `200 text/html` でログイン画面を返す**ので、`looksJson()` で型を確かめてから保存する（確かめないと
    ログイン HTML を「イベント JSON」として抱え込む）。同じ理由で `index.html` の `fetchEventText()` も
    **キャッシュへ書く前に `JSON.parse` を通す**——通さないと `markNetworkFresh()` まで走ってオフライン
    表示が消えてしまう。**タイムアウトでキャッシュを返してはいけない**——
    `index.html` 側がキャッシュ即時表示＋差分検出を持っているので、SW が同じバイト列を返すと差分が
    常に「変化なし」になり永久に更新されなくなる。**鮮度の責任は 1 層だけが持つ**。ハード失敗時のみキャッシュ。
  - `shell`（同一オリジンのその他＋ナビゲーション）＝ネットワーク優先だが **`NET_TIMEOUT_MS`(2.5秒) でキャッシュに切替**。
  - **タイムアウトは `AbortSignal` ではなく `Promise.race`** で作る。abort するとバックグラウンドのキャッシュ更新まで
    殺してしまい次回も遅いままになる。負けた側は走らせ続けてキャッシュを温める（`net.catch(()=>{})` を必ず付ける）。
  - **キャッシュは 2 本**。`SHELL_CACHE`（版ごとに捨てる）と `RUNTIME_CACHE`（版をまたいで残す。JSON・フォント・Tailwind）。
    1 本だと `CACHE_VERSION` を上げるたびにイベント JSON とフォントまで捨て、シェル更新直後だけ会場でまた遅くなる。
    **`RUNTIME_CACHE` の名前は `sw.js` と `index.html` の 2 箇所にある**（ビルド工程が無いため）ので必ず揃える。
  - **`trimRuntime()` は素直な FIFO にしてはいけない**——ランタイムで青天井に増えるのは
    **フォント実体だけ**（書影は `passthrough` なので SW キャッシュに入らない。和文フォントは
    unicode-range で 100 以上のサブセットに割れ、ウェイト 4 種で簡単に上限へ達する）。一方 Tailwind は
    install 時に**最初に**入り、イベント JSON もその直後に入るので、挿入順に消すと
    **いちばん残したい 2 つから消えて逆効果になる**。`isTrimmable()`（= `fonts.gstatic.com` のみ）で
    守る対象を除外してから古い順に削ること。
  - `handleNavigate()` の `getBrandColorCached()` は**キャッシュだけを見る（取りに行かない）**。
    以前はここで 34KB の JSON を fetch しており、初回ナビゲーションがノッチの色のために 2 本目の
    リクエスト待ちで止まっていた。色が無いときは 171KB の HTML のバッファと書き換えごと飛ばす（ストリーミングが生きる）。
  - シェル（HTML/JS/アセット）を変更したら **`CACHE_VERSION` を必ず上げる**。
- **起動経路（`index.html` の `init()`）**: **キャッシュから即描画 → 裏で最新を取得 → 生テキストの `===` で
  差分判定 → 変わっていれば静かに描き直し**。Cache API はページから直接読めるので SW の起動・制御を待たない
  （初回訪問直後は SW がまだ controller でないことがある）。
  - **「待ち切り」と「取得完了」を切り離す**——会場では「遅いが最終的には届く」が多く、締め切りで打ち切った分を
    捨てると更新が次回まで反映されず、実際には通じているのにオフライン表示が残る。締め切り（表示済み 6 秒／
    初回 10 秒）は**待つのをやめるだけ**で、届いたときの処理はいつでも走らせる。
  - **静かな再描画では `renderAll({ keepView: true })` を使う**。`setTab()` は末尾で `window.scrollTo({top:0})` まで
    行うので呼んではいけない（BOOKS を読んでいる最中にプログラムへ引き戻される）。スクロール位置は前後で保存・復元し、
    `applyAppIdentity()` は識別に関わる値（`identitySig`）が変わったときだけ回す（canvas ラスタライズを伴うため）。
  - **モーダルが開いている間は差し替えを待つ**（中身は開いた時点の `DATA` から組むため。`body.modal-open` は
    `position:fixed` なのでスクロール復元とも干渉する）。30 回待って諦める。
  - 古い版のキャッシュが今のコードで描けない場合に備え、`JSON.parse`＋`renderAll` は try/catch で囲んで通常経路へ落とす。
    `caches` は非セキュアオリジンで undefined なので全アクセスを try/catch で包む。
  - **`#errorRetry` は `location.reload()` しない**（シェルを取り直すと Tailwind CDN とフォントの代金を再度払うので、
    遅い回線ほど「再試行」が重くなる）。`init()` を呼び直す。**呼び直せるということは多重実行できるということ**なので、
    `init()` は世代番号（`initRun`）を持ち、古い実行のコールバックは何もしない。これが無いと前回の取得が
    遅れて返ったときに両方が描画し、`showLinePromo()` が二重に走ってスクロールリスナと 30 秒タイマーが
    2 本ずつ張られる（ポップアップが 2 回開く）。
  - **オフラインバナーは `navigator.onLine` だけで判定しない**——会場のキャプティブポータルや「電波は立っているが
    実質死んでいる Wi-Fi」では `true` のままで、まさに想定した場面で出なかった。`markNetworkStale()` /
    `markNetworkFresh()` で「実際に取得できたか」も混ぜる。
  - 更新トーストは `#updatedToast`。**位置決めに `transform` を使わない**——登場演出の `fadeInUp` が
    `transform` を `both` で握るので、`-translate-x-1/2` で中央寄せすると演出後に左へ飛ぶ。flex で中央寄せし、
    演出は中身のピル（`#updatedToastPill`）に当てる。
- **スタイル**: Tailwind Play CDN。アクセント色は `tailwind.config` の `theme.extend.colors.brand`。基準色は CSS 変数 `--brand`（既定 amber、`<style>` の `:root` で定義）で、`brand-50〜800` は `color-mix()` により自動生成。**イベント毎のブランド色は `events/<id>.json` の `eventInfo.brandColor`（メイン1色の16進）で指定** → `applyBrandColor()` が実行時に `--brand` を上書き（濃淡は自動）。会場/ルームのテーマ色は `index.html` の `COLOR` 辞書（`chip`/`dot`/`border`）が `tailwind.config` の `venue.*` パレット（blue/green/violet/coral）を参照。rooms の色キー `blue/green/orange/purple` を `venue-blue/green/coral/violet` にマッピング。動的生成するクラスは `tailwind.config` の `safelist` に保持（新色は両方に追加）。
- **コントラストの制約**: `brandColor` は明るい色（amber・黄）も指定されるため、**ブランド色ベタ塗り＋白文字（`--brand-fg`）を新規に増やさない**（実測 1.5〜4.4:1 で WCAG AA 未達。`updateBrandFg()` の輝度閾値 0.55 は緩く、amber でも「白」を選ぶ）。強調は**白ピル（淡地）＋ブランド濃色文字**で行い、濃色は **`color-mix(in srgb, var(--brand) 48%, black)`（＝`brand-800` 相当）**を使う（ボトムナビ・日付タブの実装を参照）。**`brand-700`（62%）は使わない**——既定の黄 `#ffd900` では白地に対し 3.45:1 で AA 未達（`brand-800` なら 5.5:1）。また、**明るいブランド色は淡地（`brand-50`〜`200`）や枠線が白い地から見分けられない**（1.0〜1.7:1）ため、ピルを浮かせるには**グレーのトラック（`bg-slate-200/60`）＋白ピル**が要る。新しい配色を足すときは、既定の黄 `#ffd900` と amber `#f59e0b` の両方で 4.5:1 以上を実測して確認する（`color-mix` の計算結果は Chrome が `oklab()` 表記で返すことがあるため、canvas に塗って RGB を取るのが確実）。
- **アニメーション**: 追加してよいのは `transform` / `opacity` のみ（GPU 合成・ビルド工程なしを維持）。タッチ／スクロール系のリスナは **`{ passive: true }` を崩さない**（スワイプは指追従せず「離した時点でコミット」する設計。`index.html` の `TAB_ORDER` とスワイプ IIFE を参照）。新規の演出クラスは `prefers-reduced-motion` ブロックへ必ず追記する（Tailwind の `transition` / `active:scale-*` はこのブロックの対象外なので取りこぼしに注意）。
- **アイコン**: 絵文字は使わず **SVG（Lucide系）**。`ICONS` レジストリ + `icon(name, cls)` ヘルパ（`index.html`）。静的箇所（ボトムナビ・FAB・モーダル閉じる）はインラインSVG。
- **マスコット（右下のふせんネコ）**: 造形の定義は **`assets/fuseneko/fuseneko-grid.js` の 1 箇所だけ**（24×24 の文字列配列 `FUSENEKO_BASE` ＋ 表情パッチ ＋ しっぽの振り）。`index.html` は `<script src>` でこれを読み、`buildCatSvg()` が待機アニメのコマを組む。配布用の SVG 資産（`assets/fuseneko/fuseneko-{base,standard,smile,serious}.svg`）は `scripts/build_fuseneko.py` が**同じ定義から生成する**ので手で編集しない（ずれたら `tests/test_fuseneko.py` が CI で落とす）。パッチは**セル単位で重ねられる**形式で、`_` は「下の絵を残す」・`.` は「透過にする」を意味する（`applyPatches()` が合成。しっぽの振りとまばたきを同じコマに同時適用できる）。塗り分けは **`--cat-base` / `--cat-fold` / `--cat-outline` / `--cat-face` / `--cat-cheek` の 5 変数**に集約し、既定値を `--brand` から `color-mix()` で作るのでイベント毎の `brandColor` に自動追従する（`fuseneko.js` の `fusenekoPalette()` が同じ比率を JS 側にも持つ。単体の SVG はフォールバック値を内蔵）。**黒に近い固定色は使わない**（重く見えるため）。ほっぺだけ固定のピンク。**24×24 のまま作り込む**（32×32 にすると 48px 表示で 1 ドット＝1.5px になり、DPR1 でドット幅が 1px/2px に割れる。整数比を保つには 64px 表示が必要で、ボトムナビ上の本文を圧迫する）。造形の決めごと（設定資料に合わせる。**色と表情以外は変えない**）: ①**胴体は col 1–17 / row 5–19 の 17×15**——ほぼ正方形でわずかに横長。幅を奇数にしてあるので中心は col 9 ちょうどで、顔の左右対称が整数で取れる。下辺は水平・左右は垂直・下の角は四角。②**右上は耳を立てず、ふせんの角を下へ折り返す**——top edge の先から `(14,6)(15,7)(16,8)(17,9)` と 1 ドットずつ階段状に切り落とし、内側を `S` で塗って row 9 の横線と col 12 の縦線で閉じる。大きな三角 1 枚にしない。ここがトレードマークなので省略しない。③左耳は col 1–4 / row 2–4 の小さな階段で、右と対称にしない。耳ぴく（`FN_EARS_DOWN`）も**左耳だけ**動かす（紙のフラップがぴくつくとおかしい）。④顔は**目＝1 ドット幅 × 3 ドット高の細い縦棒**（col 5 / col 13）、**口＝上段の 3 点（col 7 / 9 / 11）＋下段の 3 ドットの帯（col 8–10）**で ω を作る。**鼻はほっぺの色ではなく目・口と同じ濃色**（ピンクにすると猫に見えない）。ほっぺは 2×1 で輪郭に接触させない。⑤しっぽは**短く細い鉤形**——右辺の下（row 17）から真横へ出て col 20–21 で上へ折れ、row 13 で止まる。中身 1 ドット幅・全長は胴体の 1/3 程度。振り（`TAIL.up`/`down`）は**先端に 1 ドット足す／取る**だけで根元は動かさない。⑥**教科小物と番号バッジは載せない**——24px では小物に胴体左下の数ドット、バッジの数字に 3×3 しか取れず、どちらも何が描いてあるか判別できないため。表情は設定資料の 6 種（標準・にっこり・まじめ・うれしい・ひらめき・びっくり）を SVG 資産にしてあり、残り（まばたき・あくび・よそ見・耳ぴく・わくわく）は待機アニメ専用。**口を差し替えるパッチで row 14 をまとめて上書きしない**——鼻（col 9）ごと消えて猫に見えなくなる（`tests/test_fuseneko.py` が全表情で検査する）。**造形定義は外部ファイルなので、読み込みに失敗しても本文が死なないようにする**——`index.html` は `FN_OK` で通し、`setupMascot()` がマスコットだけ諦める。吹き出しの枠色（`mixWithBlack(…, 0.38)`）は `--cat-outline` と同じ比率にすること。造形の確認は `dev/fuseneko.html`（サイズ・表情・色・背景を並べる）。待機アニメは 16 コマのコマ送り（`#mascotStrip` の `translateX`）と、割り切れない周期の呼吸（`#mascotBob` の `translateY`。同一要素で `transform` を二重に持てないので入れ子にしている）を重ねる。**コマの中身は固定ではなく、`animationiteration` のたびに `shuffleCatFrames()` が選び直す**——`CAT_TAIL_TRACKS` からしっぽのリズムを 1 本引き、空きコマへ動きを置く。ふだんの動きは `CAT_ACCENTS`（まばたき／にっこり／びっくり／耳ぴく／よそ見〈左右〉／わくわく／あくび／うれしい／ひらめき）から 2〜3 個、**まれな来客**は `CAT_RARES`（ちょう／とり／ハート／おんぷ）から `CAT_RARE_CHANCE`（7%）で 1 周に最大 1 回。来客はコマ数が多いので先に場所を取る。重みは `CAT_ACCENT_POOL`/`CAT_RARE_POOL` で mood ごとに変える（終了後は「びっくり」を出さず、あくびとおんぷ中心）。動きは 1 要素＝1 コマぶんの**重ねるパッチ配列**なので、来客のようにコマごとに位置が変わるものも書ける（位置が動くパッチは `catRow()` で組み立てる）。**先頭コマには何も置かない**（周の切れ目で表情が飛び込まないように）。置き場所は空きが見つかるまで数回やり直す（1 回で諦めると 2 割強が衝突で消える）。しっぽのリズムは前周と別の 1 本を引く。つつかれたときは `reactCatFrames()` が先頭コマへ反応の絵を入れて**コマ送りを先頭から回し直す**（「いま何コマ目か」を調べずに済む。1 周後の `shuffleCatFrames()` が自然に元へ戻す）。**mood が変わると CSS が周期を差し替えるため、`restartCatAnim()` でコマ送りと呼吸を先頭から仕切り直す**——そのままだと累計経過の再解釈でコマが飛ぶ。16 コマの組み立ては 7ms 前後かかるので `requestAnimationFrame` で初回描画の後ろへ回し、組み上がってから `pop-in` で出す。差し替えは**コマ送りが先頭へ戻った瞬間**なので見た目が飛ばず、変わったコマだけ書き換える（SVG は `catSvgCache` で使い回す）。体の上下は**ふだん静止し、1 周に一度だけ 1 ドット短く沈む**（常時ゆれると「ぶれ」に見えて疲れるため）。沈んでいる時間は 1 周の 8% ほどなので、間隔が短めでも「ぶれ」には見えない。**間隔はほぼ一定**（`jitterCatBob()` が 1 回沈むごとに基準の ±12% で振り直す。既定 5 秒なら 4.4〜5.6 秒）にして規則正しい呼吸に見せ、たまに 2 回続けて沈む型（`catBob2`、12%）を混ぜる。**走行中に `animation-duration` を書き換えると「累計経過 ÷ 新しい周期」で回数が計算し直され、iteration がまとめて消化されて間隔 0 秒で何度も沈む**ので、`animation-name` を一度 `none` にして強制リフローしてから入れ直す。`prefers-reduced-motion` では作り替えない。**アニメーションイベントは親へ上がるので、リスナは必ず `e.animationName` で見分ける**（`#mascotStrip` の catIdle が `#mascotBob` にも届く）。吹き出しの文言と場面は `mascotState(now = new Date())` がイベントデータと現在時刻から算出する**純関数**で、`{ mood, lines }` を返す（`mascotLines(now)` は `lines` だけ返す薄いラッパー。`now` を渡せばコンソールから全分岐を確認できる）。`mood`（`before`/`today`/`live`/`after`/`ended`）は `#mascot` の `data-mood` に載せ、**CSS 側で待機アニメの速さだけを切り替える**（JS のタイマーは増やさない）。吹き出しもドット風で、**フォントは DotGothic16**（Google Fonts。吹き出し専用。ウェイトは 400 のみなので `font-bold` を当てない）、枠と三角のしっぽは `BUBBLE_FRAME`/`BUBBLE_ARROW` から `buildDotDataUri()` が data URI の SVG を作り、`--cat-frame`/`--cat-arrow` 経由で `border-image`（9スライス）と `background` に渡す。色はネコの輪郭と同じ計算（`mixWithBlack(resolvedBrand(), 0.6)`）。**data URI の SVG には `width`/`height` を必ず入れる**——固有サイズが無いと `border-image-slice` の数値が画像のドット数ではなく CSS ピクセル扱いになり 9 分割がずれる。表示は**イベントページのみ**で、`eventInfo.mascot: false` を置いたイベントでは出さない。文言は必ずデータから作り、`index.html` に固有文言を書かない（**キャラクター名 `CAT_NAME`＝「ふせんネコ」は例外**——イベント固有ではないので汎用シェルに置く）。**名前は隠し要素として `TAP_GAP_MS`（1.2 秒）以内に `TAPS_TO_INTRODUCE`（3 回）つつくと自分から名乗る**。名乗るときは吹き出しを強制的に開くので、折りたたみの 3 点セット（class・`aria-expanded`・localStorage）は `setupMascot()` の `setFolded()` を必ず通す。自己紹介は `mascotPinUntil`（`MASCOT_PIN_MS`＝8 秒）の間だけ 7 秒タイマーを休ませて残し、`mascotMsgs`/`mascotMsgIdx` は触らないので解除後は次の一言へ自然に戻る。`prefers-reduced-motion` では絵は変えずに文言だけ出す。名前は `#mascotBtn` の `aria-label`／`title` にも入れてある（画面に出る名前はこの 2 箇所だけ）。**ドラッグ（つまんで引っぱる）にも対応する**——`#mascotBtn`（コマ送り・呼吸）とは別に、外側の `#mascotHold` を 3 枚目の transform 層として持ち（同一要素で `transform` を二重に持てないのは他の入れ子と同じ理由）、`--mascot-dx`/`--mascot-dy`（CSS変数、`translate3d`）でずらす。位置は保存しない＝離すと必ず定位置へバネで戻る。ずらし量は**48px 表示＝1ドット2px に揃えて 2px 単位へ丸める**（他のドット表現と粒度を合わせる）。掴んでいる間は専用のコマ組み `CAT_HOLD`（しっぽを振るびっくり顔）を `holdCatFrames()` が 16 コマ全部に敷き、`shuffleCatFrames()` は `catHeld` フラグを見て待機の差し替えを止める。離すと `releaseCatFrames()` が `catHeld` を下ろし、待機アニメへ戻す。勢いよく払う（速度が `FLICK_V` を超える）と、新しい表情は作らず既存の `lookR`/`lookL`/`blink` の組み合わせだけで「目を回す」`dizzy` を `CAT_ACCENTS` に足して見せる（`CAT_ACCENT_POOL` には入れないので待機アニメには出ない）。**タブの左右スワイプ（`swipeEnabled()`）は `#mascotBtn` の上から始まった指を除外する**——除外しないとタブとネコが同じ指を取り合う。ただし `#mascotBtn` の `touch-action` は `none` ではなく **`pan-y`**（`#tabViews` と同じ値）にしてあるので、ネコの上から**縦**に払った指はブラウザの通常スクロールへ委ねられ、**横**に引いた指だけドラッグとして拾う（縦スクロールまで潰さない）。**`touch-action` だけでは足りず、JS 側にも軸判定（`DRAG_AXIS_RATIO`＝1.4、タブスワイプの `AXIS_RATIO` と同値）が要る**——ブラウザが「これは縦スクロールだ」と判断するのは数 px 動いた後で、`DRAG_MIN_PX`（6px）の閾値と競合する。軸判定が無いと、縦に払っただけで一瞬ネコが持ち上がり吹き出しが畳まれてから `pointercancel` で戻る、というちらつきが出る。縦優勢と判定した指は `pressedAt` を降ろして以降の `pointermove` を先頭で抜けさせる（押しっぱなし扱いで「なでる」が誤発火するのも防ぐ）。**隠し要素は他に 3 つ**: ①**長押し（`PET_HOLD_MS`＝0.6 秒、動かさずに押し続ける）で「なでる」**——`reactCatFrames("heart")` でハートの来客を確定で流す（`reactCatFrames()` は `CAT_ACCENTS[name] || CAT_RARES[name]` を引くので来客も同じ枠で流せる）。②**掴んで放すと吹き出しが「離す前の状態」へ静かに戻り**（畳む／保存はしない）、**勢いよく払うと目を回して一言残す**（`mascotPinUntil` で固定）。**なでる・ドラッグとも、離すと `click` が続けて飛んでくるので 1 回だけ捨てる**（`swallowClick`。捨てないと吹き出しが畳まれる／開閉が誤爆する。click が来ない離し方に備えて次の `pointerdown` でも下ろす）。ポインタ系のリスナはドラッグ判定も含めて `{ passive: true }` を保つ（`preventDefault()` は使わず `touch-action` と `setPointerCapture()` に任せる）。③**深夜・早朝の一言**（`withNightLine()`）——`mascotState()` の全分岐が通る `state()` を包んでいるので**足すのはここ 1 箇所だけ**。進行中（`live`）と文言が空のときは足さない。純関数のままなので `mascotLines(new Date("2026-08-01T02:00+09:00"))` で確認できる。**「素早く N 回」の数えは `makeTapCounter(times)` に集約**（`TAP_GAP_MS` 以内なら加算・達したら 0 に戻す）。`reactCatFrames()` は**知らない名前で呼ばれたら黙って返す**——`frames` が undefined のまま進むと例外で呼び出し元（吹き出しの開閉）ごと死ぬため。（**「ふせんネコ図鑑」は一度試作したが、静止 1 コマでは表情差分が分かりにくく削除した**。作るなら待機アニメと同じ複数コマのアニメで見せること。）
- **PWA アイデンティティ（イベント毎・実行時生成）**: `applyAppIdentity()`（`index.html`）が、アプリ名＝`logoMain`（例: 全算研2026）、アイコン＝`brandColor` 地＋`logoMain` の先頭3文字（例: 全算研）を実行時生成し、`apple-touch-icon`（canvas で PNG 化）・`apple-mobile-web-app-title`・`document.title` を差し替える。**マニフェストは `eventInfo.manifestPath`（`events/<id>.webmanifest` 実体ファイル）があればそれを参照（最も確実・iOS でも安定）**。無ければ data URI で動的生成（`start_url`/`scope` は絶対 URL 化必須——相対だと data URI 上で無効になりブラウザが静的 `manifest.json` にフォールバックしてアプリ名が「タイムテーブル」になる）。`logoMain` 未指定イベントは静的 `manifest.json`/`assets/icon.svg` にフォールバック。なお `<head>` の inline script は `?id` が妥当なら**実体の有無に関わらず** `events/<id>.webmanifest` を貼るので（iOS がパース時に読むため必要）、**行き先の確定は `applyAppIdentityInner()` 側の責務**——`logoMain` 未指定や読み込み失敗のときに `setManifestHref()` で `manifest.json` へ戻さないと、404 のマニフェストが残り、Android では `beforeinstallprompt` が発火せず「ホーム画面に追加」の導線ごと出なくなる。favicon を差し替えるときは `href` だけでなく **`type` も一緒に更新する**（静的タグは `image/jpeg` 宣言なので、SVG data URI に替えると宣言と食い違いブラウザがアイコンを採用しないことがある）。ホーム画面追加の導線は `setupInstallPrompt()`（Android=`beforeinstallprompt`、それ以外=`openInstallHelp()` で手順案内）。**主要な流入は LINE 公式アカウントのキーワード応答なので、多くの人は LINE の in-app ブラウザで最初に開く**——そこでは `beforeinstallprompt` が発火せず、iOS の共有シートにも「ホーム画面に追加」が無いため、そのままでは追加できない。`isInAppBrowser()`（UA の `Line/` ほか）で判定し、①バナーを in-app でも出す（`showInstallBanner()` の早期 return に含めない。文言も「開き方」に切り替える）②`installHelpHtml()` が **in-app×Android / in-app×iOS / iOS Safari / その他** の 4 分岐で案内を出し分ける（Android は `chromeIntentUrl()` の `intent://…;package=com.android.chrome;S.browser_fallback_url=…` で Chrome を直接開く。iOS には同等の手段が無いので URL コピー＋手順）。**根本対策は LINE 側で配る URL に `openExternalBrowser=1` を付けること**（LINE 内ブラウザを経由せず端末の Chrome / Safari で開く。`docs/event-url-index.md` の「LINE配信用URL」列がこれを生成する）。LINE 友だち追加ポップアップは `isLineApp()` のとき出さない（キーワード応答から来た人はすでに友だち）。
- **画像と転送量（会場の細い回線が前提）**: 自前のコードは軽い（`index.html` は gzip 53KB、
  イベント JSON は 8.6KB）ので、**転送量のほぼ全部は画像と外部リソース**。ここを増やさない。
  ①**告知バナーを原寸のままリポジトリに置かない**——表示枠は `w-full aspect-[2/1] max-h-72` で
  最大 672×288 CSS px しかない。`scripts/optimize_images.py` が幅 1400px へ縮小し、現行イベントは
  WebP、終了済みイベントは**同名 PNG のまま 256 色へ量子化**して書き出す（終了済みの JSON を
  編集しない規約を守るため拡張子を変えられない）。元画像は再生成のためリポジトリに残すが配信はしない。
  ②**書影は `coverUrl(url, px)` を通す**（ホスト判定は前方一致で書かない。`endsWith("toyokan.co.jp")` は
  `eviltoyokan.co.jp` を拾う）——JSON にはフルサイズ（`width=1200` / `_SL1500_` /
  `LZZZZZZZ`）の URL が入っているが表示枠は 64×96 px。描画時に小さい派生へ付け替えるので
  **JSON は書き換えない**。未知のホスト・想定外の形は素通しし、派生が 404 のときは
  `renderBooks()` が元 URL で 1 回だけ retry してからプレースホルダーに落ちる（外部 CDN の
  パラメータ仕様に賭けない）。③新しい `<img>` には `loading="lazy"` と**箱の確保**を必ず付ける。
  バナーの実寸はイベントごとに違う（1400×685 と 1400×788）ので、汎用シェルに `width`/`height` の
  数値は持てない——`aspect-[2/1]` で比率だけ固定する。④`<head>` のフォント CSS は
  `media="print"` → `onload` で `all` に戻す形にして**描画をブロックさせない**（`display=swap` と
  併せて本文は即出る）。接続確立が高くつくので `preconnect`（フォント・Tailwind）と
  `dns-prefetch`（画像ホスト）を置くが、preconnect は張りすぎると逆効果なので増やさない。
  なお **Tailwind Play CDN（約120KB gzip ＋実行時 JIT）が初回表示の最大のボトルネック**で、
  同じ設定からローカルビルドすると 26KB まで落ちる。ビルド工程なしを優先して CDN のままにしてあるので、
  やるなら生成物をコミットする方式（`build_fuseneko.py` と同じ作法）にすること。
- **描画の安全性**: 文字列は必ず `escapeHtml()`（`index.html`）を通して DOM に入れる。
- **DOM 生成ヘルパ**: `el(tag, class, html)` と `$(id)`（= `getElementById`）を再利用する。

## ファイルマップ
| ファイル | 役割 | 編集方針 |
| --- | --- | --- |
| `index.html` | 汎用 UI シェル + 描画ロジック | ⚠️ ロジック変更時のみ。**固有文言は書かない** |
| `events.json` | イベント一覧インデックス（スクリプト・URL台帳生成用。UI の一覧表示には未使用） | ✅ イベント追加時に1エントリ追記 |
| `events/<id>.json` | 各イベントの全情報（`eventInfo`/`rooms`/`sessions`/`books`） | ✅ ここを追加・編集 |
| `sw.js` | Service Worker（Network First） | ⚠️ 変更時は `CACHE_VERSION` を上げる |
| `manifest.json` | PWA 汎用シェル（インストール名・色） | △ 任意 |
| `assets/` | アイコン・会場マップ（SVG） | △ 任意 |
| `assets/fuseneko/fuseneko-grid.js` | ふせんネコの造形（**唯一の定義**） | ⚠️ 造形を変えるときだけ。SVG 資産の再生成が要る |
| `assets/fuseneko/fuseneko-*.svg` | 配布用 SVG（生成物） | ⛔ 手で編集しない。`python3 scripts/build_fuseneko.py` で作る |
| `assets/fuseneko/fuseneko.js` / `variants.js` | `createFuseneko()` とバリエーション表 | △ 色・表情を足すとき |
| `dev/fuseneko.html` | ふせんネコの確認ページ | △ 任意 |

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
