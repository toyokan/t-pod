#!/usr/bin/env python3
"""イベントJSON・一覧・PWAアセットの整合性を検証する。

使い方:
    python scripts/validate_events.py
    python scripts/validate_events.py --event 2026-zensanken-37
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
EVENTS_INDEX = ROOT / "events.json"
EVENTS_DIR = ROOT / "events"
ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
TIME_RE = re.compile(r"^(?:[01]?\d|2[0-3]):[0-5]\d$")
ROOM_COLORS = {"blue", "blueDeep", "green", "greenDeep", "orange", "purple"}
NOTICE_LEVELS = {"important", "info"}
PLACEHOLDER_MARKERS = ("example", "xxxx", "your-", "<id>")


@dataclass
class Finding:
    level: str
    location: str
    message: str


class Validator:
    """検証結果を収集する。"""

    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def error(self, location: str, message: str) -> None:
        self.findings.append(Finding("ERROR", location, message))

    def warn(self, location: str, message: str) -> None:
        self.findings.append(Finding("WARN", location, message))

    def require_str(self, obj: dict[str, Any], key: str, location: str) -> str:
        value = obj.get(key)
        if not isinstance(value, str) or not value.strip():
            self.error(f"{location}.{key}", "空でない文字列が必要です")
            return ""
        return value.strip()

    def check_url(self, value: Any, location: str, *, allow_relative: bool = False) -> None:
        if not isinstance(value, str) or not value.strip():
            self.error(location, "URLが空です")
            return
        url = value.strip()
        parsed = urlparse(url)
        if allow_relative and not parsed.scheme:
            if url.startswith(("/", "../")) or ".." in Path(url).parts:
                self.error(location, "リポジトリ内パスはルート相対や親参照を使わないでください")
            return
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            self.error(location, "http(s)の公開URLが必要です")
        if any(marker in url.lower() for marker in PLACEHOLDER_MARKERS):
            self.warn(location, "仮URLらしい文字列が残っています")


def normalize_display_text(value: Any) -> str:
    """全角半角と空白だけの表記差を比較用に吸収する。"""
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value))


def load_json(path: Path, validator: Validator, location: str) -> Any:
    """JSONを読み、失敗を検証結果へ追加する。"""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        validator.error(location, f"ファイルがありません: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        validator.error(location, f"JSON構文エラー: {exc.msg} (行{exc.lineno}, 列{exc.colno})")
    return None


def validate_event_data(
    event_id: str,
    data: Any,
    index_entry: dict[str, Any],
    validator: Validator,
) -> None:
    """個別イベントJSONを検証する。"""
    base = f"events/{event_id}.json"
    if not isinstance(data, dict):
        validator.error(base, "ルートはオブジェクトである必要があります")
        return

    info = data.get("eventInfo")
    if not isinstance(info, dict):
        validator.error(f"{base}.eventInfo", "オブジェクトが必要です")
        return

    required_info = ("title", "logoMain", "brandColor", "theme", "venueName", "dateRange")
    for key in required_info:
        validator.require_str(info, key, f"{base}.eventInfo")
    brand_color = info.get("brandColor")
    if isinstance(brand_color, str) and not HEX_RE.fullmatch(brand_color):
        validator.error(f"{base}.eventInfo.brandColor", "# + 6桁16進で指定してください")

    for key in ("title", "venueName", "brandColor"):
        if info.get(key) != index_entry.get(key):
            validator.error(
                f"{base}.eventInfo.{key}",
                f"events.json の値と一致しません ({index_entry.get(key)!r})",
            )
    for key in ("theme", "dateRange"):
        if normalize_display_text(info.get(key)) != normalize_display_text(index_entry.get(key)):
            validator.warn(
                f"{base}.eventInfo.{key}",
                f"events.json と表記または内容が異なります ({index_entry.get(key)!r})",
            )

    dates = info.get("dates")
    if not isinstance(dates, list) or not dates:
        validator.error(f"{base}.eventInfo.dates", "1件以上の配列が必要です")
        dates = []
    date_ids: set[str] = set()
    for i, item in enumerate(dates):
        loc = f"{base}.eventInfo.dates[{i}]"
        if not isinstance(item, dict):
            validator.error(loc, "オブジェクトが必要です")
            continue
        date_id = validator.require_str(item, "id", loc)
        if date_id in date_ids:
            validator.error(f"{loc}.id", "日付IDが重複しています")
        date_ids.add(date_id)
        validator.require_str(item, "label", loc)
        raw_date = validator.require_str(item, "date", loc)
        try:
            date.fromisoformat(raw_date)
        except ValueError:
            validator.error(f"{loc}.date", "YYYY-MM-DDの実在日付が必要です")
        validator.require_str(item, "weekday", loc)
        validator.require_str(item, "time", loc)

    rooms = data.get("rooms", [])
    if rooms is None:
        rooms = []
    if not isinstance(rooms, list):
        validator.error(f"{base}.rooms", "配列が必要です")
        rooms = []
    room_ids: set[str] = set()
    for i, room in enumerate(rooms):
        loc = f"{base}.rooms[{i}]"
        if not isinstance(room, dict):
            validator.error(loc, "オブジェクトが必要です")
            continue
        room_id = validator.require_str(room, "id", loc)
        if room_id in room_ids:
            validator.error(f"{loc}.id", "会場IDが重複しています")
        room_ids.add(room_id)
        validator.require_str(room, "name", loc)
        color = validator.require_str(room, "color", loc)
        if color and color not in ROOM_COLORS:
            validator.error(f"{loc}.color", f"許可値: {', '.join(sorted(ROOM_COLORS))}")

    sessions = data.get("sessions")
    if not isinstance(sessions, list) or not sessions:
        validator.error(f"{base}.sessions", "1件以上の配列が必要です")
        sessions = []
    session_ids: set[str] = set()
    for i, session in enumerate(sessions):
        loc = f"{base}.sessions[{i}]"
        if not isinstance(session, dict):
            validator.error(loc, "オブジェクトが必要です")
            continue
        session_id = validator.require_str(session, "id", loc)
        if session_id in session_ids:
            validator.error(f"{loc}.id", "セッションIDが重複しています")
        session_ids.add(session_id)
        date_id = validator.require_str(session, "dateId", loc)
        if date_id and date_id not in date_ids:
            validator.error(f"{loc}.dateId", "開催日に存在しない日付IDです")
        validator.require_str(session, "category", loc)
        for time_key in ("start", "end"):
            raw_time = session.get(time_key, "")
            if not isinstance(raw_time, str):
                validator.error(f"{loc}.{time_key}", "文字列が必要です")
            elif raw_time and not TIME_RE.fullmatch(raw_time):
                validator.error(f"{loc}.{time_key}", "H:MM または HH:MM で指定してください")
        if "afterNote" in session and not isinstance(session["afterNote"], str):
            validator.error(f"{loc}.afterNote", "文字列が必要です")
        items = session.get("items")
        if not isinstance(items, list):
            validator.error(f"{loc}.items", "配列が必要です。項目なしは [] にします")
            continue
        for j, item in enumerate(items):
            item_loc = f"{loc}.items[{j}]"
            if not isinstance(item, dict):
                validator.error(item_loc, "オブジェクトが必要です")
                continue
            room = item.get("room")
            if room is not None and (not isinstance(room, str) or room not in room_ids):
                validator.error(f"{item_loc}.room", "rooms[] に存在する会場IDが必要です")
            if "title" in item and not isinstance(item["title"], str):
                validator.error(f"{item_loc}.title", "文字列が必要です")
            meta = item.get("meta", [])
            invalid_meta = not isinstance(meta, list) or any(
                not isinstance(line, str) or not line for line in meta
            )
            if invalid_meta:
                validator.error(f"{item_loc}.meta", "空でない文字列の配列が必要です")
            if "subtle" in item and not isinstance(item["subtle"], bool):
                validator.error(f"{item_loc}.subtle", "true / false の真偽値が必要です")

    notices = info.get("notices", [])
    if not isinstance(notices, list):
        validator.error(f"{base}.eventInfo.notices", "配列が必要です")
    else:
        for i, notice in enumerate(notices):
            loc = f"{base}.eventInfo.notices[{i}]"
            if not isinstance(notice, dict):
                validator.error(loc, "オブジェクトが必要です")
                continue
            validator.require_str(notice, "title", loc)
            validator.require_str(notice, "body", loc)
            if notice.get("level") not in NOTICE_LEVELS:
                validator.error(f"{loc}.level", "important または info が必要です")

    venue = info.get("venue", {})
    if not isinstance(venue, dict):
        validator.error(f"{base}.eventInfo.venue", "オブジェクトが必要です")
    else:
        if "mapImage" in venue:
            validator.check_url(
                venue["mapImage"],
                f"{base}.eventInfo.venue.mapImage",
                allow_relative=True,
            )
            map_image = venue["mapImage"]
            if isinstance(map_image, str) and not urlparse(map_image).scheme:
                if not (ROOT / map_image).is_file():
                    validator.error(f"{base}.eventInfo.venue.mapImage", "指定された画像ファイルがありません")
        validate_links(
            venue.get("resourceLinks", []),
            f"{base}.eventInfo.venue.resourceLinks",
            validator,
        )
    validate_links(info.get("forms", []), f"{base}.eventInfo.forms", validator)
    book_sale = info.get("bookSale")
    if book_sale is not None:
        if not isinstance(book_sale, dict):
            validator.error(f"{base}.eventInfo.bookSale", "オブジェクトが必要です")
        else:
            validator.check_url(book_sale.get("url"), f"{base}.eventInfo.bookSale.url")

    books = data.get("books", [])
    if not isinstance(books, list):
        validator.error(f"{base}.books", "配列が必要です")
    else:
        for i, book in enumerate(books):
            loc = f"{base}.books[{i}]"
            if not isinstance(book, dict):
                validator.error(loc, "オブジェクトが必要です")
                continue
            for key in ("title", "author", "publisher", "description"):
                validator.require_str(book, key, loc)
            for key in ("cover", "url", "amazon_url"):
                if key in book:
                    validator.check_url(book[key], f"{loc}.{key}")

    manifest_path = info.get("manifestPath")
    if not isinstance(manifest_path, str) or manifest_path != f"events/{event_id}.webmanifest":
        validator.error(
            f"{base}.eventInfo.manifestPath",
            f"events/{event_id}.webmanifest を指定してください",
        )
    else:
        validate_manifest(event_id, info, ROOT / manifest_path, validator)


def validate_links(links: Any, location: str, validator: Validator) -> None:
    """ラベル付きリンク配列を検証する。"""
    if not isinstance(links, list):
        validator.error(location, "配列が必要です")
        return
    for i, link in enumerate(links):
        loc = f"{location}[{i}]"
        if not isinstance(link, dict):
            validator.error(loc, "オブジェクトが必要です")
            continue
        validator.require_str(link, "label", loc)
        if "description" in link and not isinstance(link["description"], str):
            validator.error(f"{loc}.description", "文字列が必要です")
        validator.check_url(link.get("url"), f"{loc}.url")


def validate_manifest(
    event_id: str,
    info: dict[str, Any],
    path: Path,
    validator: Validator,
) -> None:
    """イベント別マニフェストとアイコンを検証する。"""
    rel = path.relative_to(ROOT).as_posix()
    manifest = load_json(path, validator, rel)
    if not isinstance(manifest, dict):
        return
    expected_start = f"../?id={event_id}"
    if manifest.get("start_url") != expected_start:
        validator.error(f"{rel}.start_url", f"{expected_start!r} が必要です")
    if manifest.get("scope") != "../":
        validator.error(f"{rel}.scope", "'../' が必要です")
    if manifest.get("display") != "standalone":
        validator.error(f"{rel}.display", "'standalone' が必要です")
    if manifest.get("theme_color") != info.get("brandColor"):
        validator.error(f"{rel}.theme_color", "eventInfo.brandColor と一致しません")
    expected_name = info.get("appName") or info.get("logoMain")
    if manifest.get("name") != expected_name or manifest.get("short_name") != expected_name:
        validator.error(f"{rel}.name", "appName（未指定時はlogoMain）と一致しません")

    icons = manifest.get("icons")
    if not isinstance(icons, list) or not icons:
        validator.error(f"{rel}.icons", "1件以上のアイコンが必要です")
        return
    icon_src = f"../assets/icon-{event_id}.svg"
    if not any(isinstance(icon, dict) and icon.get("src") == icon_src for icon in icons):
        validator.error(f"{rel}.icons", f"{icon_src!r} を参照するアイコンが必要です")
    icon_path = ROOT / "assets" / f"icon-{event_id}.svg"
    if not icon_path.is_file():
        validator.error(f"assets/icon-{event_id}.svg", "アイコンファイルがありません")
    else:
        svg = icon_path.read_text(encoding="utf-8")
        if info.get("brandColor", "").lower() not in svg.lower():
            validator.error(f"assets/icon-{event_id}.svg", "eventInfo.brandColor が使われていません")
        label = info.get("iconLabel") or str(info.get("logoMain", ""))[:3]
        if label and label not in svg:
            validator.warn(f"assets/icon-{event_id}.svg", "iconLabel（未指定時はlogoMain先頭3文字）が見つかりません")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", help="指定したイベントIDだけを検証")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validator = Validator()
    index = load_json(EVENTS_INDEX, validator, "events.json")
    if not isinstance(index, dict) or not isinstance(index.get("events"), list):
        validator.error("events.json.events", "配列が必要です")
        entries: list[Any] = []
    else:
        entries = index["events"]

    seen_ids: set[str] = set()
    selected = 0
    for i, entry in enumerate(entries):
        loc = f"events.json.events[{i}]"
        if not isinstance(entry, dict):
            validator.error(loc, "オブジェクトが必要です")
            continue
        event_id = validator.require_str(entry, "id", loc)
        if not ID_RE.fullmatch(event_id):
            validator.error(f"{loc}.id", "半角英数・ハイフン・アンダースコアのみ使用できます")
        if event_id in seen_ids:
            validator.error(f"{loc}.id", "イベントIDが重複しています")
        seen_ids.add(event_id)
        if args.event and event_id != args.event:
            continue
        selected += 1
        for key in ("title", "theme", "dateRange", "venueName"):
            validator.require_str(entry, key, loc)
        raw_sort_date = validator.require_str(entry, "sortDate", loc)
        try:
            date.fromisoformat(raw_sort_date)
        except ValueError:
            validator.error(f"{loc}.sortDate", "YYYY-MM-DDの実在日付が必要です")
        color = validator.require_str(entry, "brandColor", loc)
        if color and not HEX_RE.fullmatch(color):
            validator.error(f"{loc}.brandColor", "# + 6桁16進で指定してください")
        data = load_json(EVENTS_DIR / f"{event_id}.json", validator, f"events/{event_id}.json")
        validate_event_data(event_id, data, entry, validator)

    if args.event and selected == 0:
        validator.error("--event", f"events.json に {args.event!r} がありません")

    for finding in validator.findings:
        print(f"{finding.level}: {finding.location}: {finding.message}")
    error_count = sum(item.level == "ERROR" for item in validator.findings)
    warning_count = sum(item.level == "WARN" for item in validator.findings)
    print(f"検証完了: {selected}イベント / エラー{error_count}件 / 警告{warning_count}件")
    return 1 if error_count else 0


if __name__ == "__main__":
    sys.exit(main())
