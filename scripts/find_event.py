#!/usr/bin/env python3
"""キーワードから編集対象のイベントを特定する（読み取り専用）。

似た名称（全国算数／算数サマーフェス）や年度違いのイベントを取り違えないための
補助ツール。編集着手前に、正しい id とファイルパスを決定的に確認する。

使い方:
    python scripts/find_event.py "算数 2026"   # キーワード検索
    python scripts/find_event.py 国語
    python scripts/find_event.py --upcoming     # 今日基準で開催中／直近の現行イベント
    python scripts/find_event.py --current       # 今日開催中（±開催期間）のイベント

終了判定: 最終開催日（個別JSONの eventInfo.dates[] の最終 date、無ければ
events.json の sortDate）＋7日 < 今日 なら「終了済」とみなす。

終了コード:
    0  単一に絞れた（または一覧表示）
    2  候補が複数で曖昧（取り違え注意）／該当なし
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from datetime import date, timedelta
from pathlib import Path
from typing import Any

try:  # Windows の cp932 端末でも UTF-8 で出力する
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]
EVENTS_INDEX = ROOT / "events.json"
EVENTS_DIR = ROOT / "events"
ENDED_GRACE_DAYS = 7


def normalize(value: Any) -> str:
    """全角半角・大文字小文字・空白差を吸収して比較用に正規化する。"""
    if not isinstance(value, str):
        return ""
    return unicodedata.normalize("NFKC", value).lower().replace(" ", "").replace("　", "")


_EVENT_CACHE: dict[str, dict[str, Any]] = {}


def load_event(entry: dict[str, Any]) -> dict[str, Any]:
    """個別イベントJSONを読む（読めなければ空）。同じidは読み直さない。"""
    event_id = str(entry.get("id", ""))
    if event_id in _EVENT_CACHE:
        return _EVENT_CACHE[event_id]
    data: dict[str, Any] = {}
    path = EVENTS_DIR / f"{event_id}.json"
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except (json.JSONDecodeError, OSError):
            pass
    _EVENT_CACHE[event_id] = data
    return data


def manual_status(entry: dict[str, Any]) -> str:
    """個別JSONルートの _status（手動固定）を返す。無ければ空文字。

    中止・延期・恒久保留などの特殊ケース用で、日付判定より優先する
    （index.html のマスコット場面判定と同じ規則）。
    """
    value = load_event(entry).get("_status")
    return value if value in ("ended", "active") else ""


def last_event_date(entry: dict[str, Any]) -> date | None:
    """イベントの最終開催日を返す（個別JSONの dates 優先、無ければ sortDate）。"""
    dates: list[date] = []
    for item in load_event(entry).get("eventInfo", {}).get("dates", []) or []:
        try:
            dates.append(date.fromisoformat(str(item.get("date", ""))))
        except (ValueError, TypeError, AttributeError):
            continue
    if dates:
        return max(dates)
    try:
        return date.fromisoformat(str(entry.get("sortDate", "")))
    except ValueError:
        return None


def start_event_date(entry: dict[str, Any]) -> date | None:
    """イベントの開始日（sortDate）を返す。"""
    try:
        return date.fromisoformat(str(entry.get("sortDate", "")))
    except ValueError:
        return None


def is_ended(entry: dict[str, Any], today: date) -> bool:
    """最終開催日＋7日を過ぎていれば終了済みとみなす（_status があればそちらが優先）。"""
    status = manual_status(entry)
    if status:
        return status == "ended"
    last = last_event_date(entry)
    if last is None:
        return False
    return last + timedelta(days=ENDED_GRACE_DAYS) < today


def status_label(entry: dict[str, Any], today: date) -> str:
    """終了済／開催中／今後 のラベルを返す。"""
    status = manual_status(entry)
    if status == "ended":
        return "終了済(手動固定)"
    if status == "active":
        return "現行(手動固定)"
    start = start_event_date(entry)
    last = last_event_date(entry)
    if last is not None and last + timedelta(days=ENDED_GRACE_DAYS) < today:
        return "終了済"
    if start is not None and last is not None and start <= today <= last:
        return "開催中"
    if last is not None and today > last:
        return "終了直後(猶予中・編集可)"
    return "今後"


def score(entry: dict[str, Any], query: str) -> int:
    """キーワードとの一致度を返す（大きいほど適合）。"""
    q = normalize(query)
    if not q:
        return 0
    terms = [t for t in q.replace("　", " ").split() if t] or [q]
    total = 0
    fields = {
        "id": str(entry.get("id", "")),
        "title": str(entry.get("title", "")),
        "theme": str(entry.get("theme", "")),
        "venueName": str(entry.get("venueName", "")),
        "dateRange": str(entry.get("dateRange", "")),
    }
    normed = {k: normalize(v) for k, v in fields.items()}
    for term in terms:
        if term in normed["id"]:
            total += 5
        if term in normed["title"]:
            total += 3
        if term in normed["theme"] or term in normed["venueName"]:
            total += 1
        if term in normed["dateRange"]:
            total += 1
    return total


def print_entry(entry: dict[str, Any], today: date) -> None:
    """候補1件を整形表示する。"""
    event_id = str(entry.get("id", ""))
    print(f"  id        : {event_id}")
    print(f"  file      : events/{event_id}.json")
    print(f"  title     : {entry.get('title', '')}")
    print(f"  dateRange : {entry.get('dateRange', '')}")
    print(f"  sortDate  : {entry.get('sortDate', '')}")
    print(f"  status    : {status_label(entry, today)}")
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", nargs="*", help="検索キーワード（例: 算数 2026）")
    parser.add_argument("--upcoming", action="store_true", help="今日基準で開催中／直近の現行イベントを表示")
    parser.add_argument("--current", action="store_true", help="今日開催中のイベントを表示")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    today = date.today()
    try:
        index = json.loads(EVENTS_INDEX.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"events.json を読めません: {exc}", file=sys.stderr)
        return 2
    entries = [e for e in index.get("events", []) if isinstance(e, dict)]

    if args.current:
        matches = [
            e for e in entries
            if (s := start_event_date(e)) and (l := last_event_date(e)) and s <= today <= l
        ]
        if not matches:
            print("本日開催中のイベントはありません。")
            return 2
        print(f"本日開催中のイベント（{today.isoformat()}）:\n")
        for e in matches:
            print_entry(e, today)
        return 0

    if args.upcoming:
        future = [
            (start_event_date(e), e) for e in entries
            if not is_ended(e, today) and start_event_date(e) is not None
        ]
        future.sort(key=lambda pair: pair[0])
        if not future:
            print("現行（未終了）のイベントはありません。")
            return 2
        print(f"現行（未終了）のイベント（{today.isoformat()} 基準・開催日順）:\n")
        for _, e in future:
            print_entry(e, today)
        return 0

    query = " ".join(args.query).strip()
    if not query:
        print("検索キーワード、または --upcoming / --current を指定してください。", file=sys.stderr)
        return 2

    scored = sorted(
        ((score(e, query), e) for e in entries),
        key=lambda pair: pair[0],
        reverse=True,
    )
    hits = [(s, e) for s, e in scored if s > 0]
    if not hits:
        print(f"「{query}」に一致するイベントはありません。events.json を確認してください。")
        return 2

    top = hits[0][0]
    best = [e for s, e in hits if s == top]
    others = [e for s, e in hits if s < top]

    if len(best) == 1:
        print(f"「{query}」の最有力候補:\n")
        print_entry(best[0], today)
        if others:
            print("※ 部分一致した他候補（取り違え注意）:")
            for e in others:
                print(f"  - {e.get('id')} … {e.get('title')}")
        return 0

    print(f"[!] 「{query}」に同点で複数一致しました。取り違え注意——id を明示して特定してください:\n")
    for e in best:
        print_entry(e, today)
    return 2


if __name__ == "__main__":
    sys.exit(main())
