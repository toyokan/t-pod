## 目的

## 対象

<!-- イベントデータの変更なら id・title・開催日を書く（似た名称・別年度との取り違え防止。CLAUDE.md「対象イベントの特定」） -->

## 確認したこと

- [ ] `python scripts/validate_events.py` と `python -m unittest discover -s tests` が通る
- [ ] 終了済みイベント（最終開催日＋7日超）の `events/<id>.json` を編集していない
- [ ] シェル（`index.html` / `sw.js` / `assets/`）を変えた場合は `sw.js` の `CACHE_VERSION` を上げた
- [ ] 既存の URL（`?id=`）・localStorage のキー・`events/<id>.json` の形式を壊していない
- [ ] 外部送信・外部依存を増やしていない（増やした場合は README「データの扱い」を更新）
- [ ] スマートフォン（iPhone Safari／LINE 内ブラウザ）で表示を確認した
- [ ] 開催当日・前日のシェル変更なら、マージのタイミングを相談した
