#!/usr/bin/env python3
"""events.json から開発者向けイベントURL台帳を生成する。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

try:  # Windows の cp932 端末でも UTF-8 で出力する
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]
EVENTS_INDEX = ROOT / "events.json"
OUTPUT_PATH = ROOT / "docs" / "event-url-index.md"
def render_event_url_index(index: dict[str, Any]) -> str:
    """イベント索引からURL台帳のMarkdownを返す。"""
    base_url = str(index.get("siteUrl", "")).rstrip("/") + "/"
    entries = sorted(
        index.get("events", []),
        key=lambda entry: (str(entry.get("sortDate", "")), str(entry.get("id", ""))),
        reverse=True,
    )
    lines = [
        "# 開発者向けイベントURL台帳",
        "",
        "`events.json` から自動生成しています。直接編集せず、生成スクリプトを実行してください。",
        "",
        "| イベント名 | 開催日 | イベントID | 本番URL |",
        "| --- | --- | --- | --- |",
    ]
    for entry in entries:
        event_id = str(entry.get("id", ""))
        title = str(entry.get("title", "")).replace("|", "\\|")
        date_range = str(entry.get("dateRange", "")).replace("|", "\\|")
        url = f"{base_url}?id={quote(event_id, safe='')}"
        lines.append(f"| {title} | {date_range} | `{event_id}` | [サイトを開く]({url}) |")
    lines.append("")
    return "\n".join(lines)


def write_event_url_index(index: dict[str, Any]) -> None:
    """URL台帳をUTF-8・LFで書き出す。"""
    OUTPUT_PATH.write_text(render_event_url_index(index), encoding="utf-8", newline="\n")


def main() -> int:
    """events.json を読み、URL台帳を更新する。"""
    index = json.loads(EVENTS_INDEX.read_text(encoding="utf-8"))
    write_event_url_index(index)
    print(f"更新しました: {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
