#!/usr/bin/env python3
"""ふせんネコの SVG 資産を assets/fuseneko/fuseneko-grid.js から生成する。

grid が唯一の定義なので、生成物（fuseneko-base.svg など）は手で編集しない。

    python3 scripts/build_fuseneko.py            # 生成（書き込み）
    python3 scripts/build_fuseneko.py --check    # 生成物が grid とずれていないか検査
    python3 scripts/build_fuseneko.py --preview  # ターミナルにドット絵を描く
    python3 scripts/build_fuseneko.py --preview smile ears
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRID_JS = ROOT / "assets" / "fuseneko" / "fuseneko-grid.js"
OUT_DIR = ROOT / "assets" / "fuseneko"

GRID = 24

# 生成する SVG と、そこに重ねる表情パッチの名前
SVG_TARGETS = {
    "fuseneko-base": [],
    "fuseneko-standard": [],
    "fuseneko-smile": ["FN_SMILE"],
    "fuseneko-serious": ["FN_SERIOUS"],
}

# 単体で <img> 表示されたときのための既定色（標準の黄から作る）。
# ページ側が --cat-* を定義していればそちらが優先される。
# 混色比は assets/fuseneko/fuseneko.js の MIX と同じ値にすること——
# 片方だけ変えるとアプリ内のマスコットと配布用 SVG で色がずれる。
DEFAULT_THEME = (0xFF, 0xD9, 0x00)
MIX = {
    "base": ((255, 255, 255), 0.48),
    "outline": ((0, 0, 0), 0.62),
    "face": ((0, 0, 0), 0.74),
}


def _mix(rgb, target, ratio):
    return "#" + "".join(f"{round(v * (1 - ratio) + t * ratio):02x}" for v, t in zip(rgb, target))


def _palette():
    return {
        "base": _mix(DEFAULT_THEME, *MIX["base"]),
        "fold": "#" + "".join(f"{v:02x}" for v in DEFAULT_THEME),
        "outline": _mix(DEFAULT_THEME, *MIX["outline"]),
        "face": _mix(DEFAULT_THEME, *MIX["face"]),
        "cheek": "#f7a8b8",
        "white": "#ffffff",
    }


_PAL = _palette()
FILL_CSS = [
    ("fn-base", "--cat-base", _PAL["base"]),
    ("fn-fold", "--cat-fold", _PAL["fold"]),
    ("fn-outline", "--cat-outline", _PAL["outline"]),
    ("fn-cheek", "--cat-cheek", _PAL["cheek"]),
    ("fn-face", "--cat-face", _PAL["face"]),
    ("fn-white", "--cat-white", _PAL["white"]),
]

# ターミナル表示用（1 ドット = 2 文字）
GLYPH = {".": "  ", "K": "██", "B": "░░", "S": "▒▒", "E": "▓▓", "P": "@@", "W": "::"}


def _strings(block: str) -> list[str]:
    return re.findall(r'"([^"]*)"', block)


def parse_grid_js(text: str) -> dict:
    """grid の JS から配列・オブジェクト定数を抜き出す。

    形式が変わって拾えなくなったら黙って壊れないよう、必ず存在検査をする。
    """
    arrays: dict[str, list[str]] = {}
    for name, body in re.findall(r"const (\w+) = \[(.*?)\];", text, re.S):
        rows = _strings(body)
        if rows and all(len(r) == GRID for r in rows):
            arrays[name] = rows

    patches: dict[str, dict[int, str]] = {}
    for name, body in re.findall(r"const (\w+) = \{(.*?)\};", text, re.S):
        entries = re.findall(r"(\d+):\s*\"([^\"]*)\"", body)
        if entries:
            patches[name] = {int(row): value for row, value in entries}

    if "FUSENEKO_BASE" not in arrays:
        raise SystemExit("FUSENEKO_BASE が読み取れませんでした（fuseneko-grid.js の書式を確認）")
    return {"arrays": arrays, "patches": patches}


def validate(parsed: dict) -> list[str]:
    """グリッドの体裁を検査してエラー文字列を返す。"""
    errors: list[str] = []
    base = parsed["arrays"]["FUSENEKO_BASE"]
    if len(base) != GRID:
        errors.append(f"FUSENEKO_BASE の行数が {len(base)}（{GRID} 行であるべき）")
    for i, row in enumerate(base):
        if len(row) != GRID:
            errors.append(f"FUSENEKO_BASE row {i} が {len(row)} 文字（{GRID} 文字であるべき）")
        for ch in row:
            if ch not in GLYPH:
                errors.append(f"FUSENEKO_BASE row {i} に未定義の文字 {ch!r}")
    for name, patch in parsed["patches"].items():
        for row, value in patch.items():
            if len(value) != GRID:
                errors.append(f"{name} row {row} が {len(value)} 文字（{GRID} 文字であるべき）")
            if not 0 <= row < GRID:
                errors.append(f"{name} の行 {row} がグリッド外")
            for ch in value:
                if ch != "_" and ch not in GLYPH:
                    errors.append(f"{name} row {row} に未定義の文字 {ch!r}")
    return errors


def apply_patches(base: list[str], patches: list[dict[int, str]]) -> list[str]:
    rows = list(base)
    for patch in patches:
        for y, value in patch.items():
            rows[y] = "".join(
                rows[y][x] if value[x] == "_" else value[x] for x in range(GRID)
            )
    return rows


def to_rects(rows: list[str], indent: str = "  ") -> str:
    fill = {"K": "fn-outline", "B": "fn-base", "S": "fn-fold", "P": "fn-cheek", "E": "fn-face", "W": "fn-white"}
    out = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            ch = row[x]
            w = 1
            while x + w < len(row) and row[x + w] == ch:
                w += 1
            cls = fill.get(ch)
            if cls:
                out.append(f'{indent}<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="1"/>')
            x += w
    return "\n".join(out)


def build_svg(rows: list[str], title: str) -> str:
    style = "\n".join(
        f"    .{cls} {{ fill: var({var}, {default}); }}" for cls, var, default in FILL_CSS
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"\n'
        '     shape-rendering="crispEdges" role="img" aria-label="' + title + '">\n'
        f"  <title>{title}</title>\n"
        "  <style>\n"
        f"{style}\n"
        "  </style>\n"
        f"{to_rects(rows)}\n"
        "</svg>\n"
    )


TITLES = {
    "fuseneko-base": "ふせんネコ（基本シルエット）",
    "fuseneko-standard": "ふせんネコ（標準）",
    "fuseneko-smile": "ふせんネコ（にっこり）",
    "fuseneko-serious": "ふせんネコ（まじめ）",
}


def render(parsed: dict) -> dict[str, str]:
    base = parsed["arrays"]["FUSENEKO_BASE"]
    out = {}
    for name, patch_names in SVG_TARGETS.items():
        patches = []
        for pn in patch_names:
            if pn not in parsed["patches"]:
                raise SystemExit(f"{pn} が fuseneko-grid.js に見つかりません")
            patches.append(parsed["patches"][pn])
        out[name] = build_svg(apply_patches(base, patches), TITLES[name])
    return out


def preview(parsed: dict, names: list[str]) -> None:
    base = parsed["arrays"]["FUSENEKO_BASE"]
    patches = []
    for n in names:
        key = n if n in parsed["patches"] else f"FN_{n.upper()}"
        if key not in parsed["patches"]:
            raise SystemExit(f"{n} が見つかりません（候補: {', '.join(sorted(parsed['patches']))}）")
        patches.append(parsed["patches"][key])
    rows = apply_patches(base, patches)
    label = " + ".join(names) if names else "FUSENEKO_BASE"
    print(f"\n== {label} ==")
    print("    " + "".join(f"{c % 10}" * 2 for c in range(GRID)))
    for y, row in enumerate(rows):
        print(f"{y:>3} " + "".join(GLYPH[ch] for ch in row))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="生成物が grid とずれていないか検査する")
    ap.add_argument("--preview", nargs="*", metavar="PATCH", help="ターミナルにドット絵を描く")
    args = ap.parse_args()

    parsed = parse_grid_js(GRID_JS.read_text(encoding="utf-8"))
    errors = validate(parsed)
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if args.preview is not None:
        preview(parsed, args.preview)
        return 0

    rendered = render(parsed)
    if args.check:
        stale = []
        for name, svg in rendered.items():
            path = OUT_DIR / f"{name}.svg"
            if not path.exists() or path.read_text(encoding="utf-8") != svg:
                stale.append(path.relative_to(ROOT).as_posix())
        if stale:
            print("生成物が fuseneko-grid.js とずれています:", file=sys.stderr)
            for s in stale:
                print(f"  {s}", file=sys.stderr)
            print("`python3 scripts/build_fuseneko.py` で再生成してください。", file=sys.stderr)
            return 1
        print(f"OK: SVG {len(rendered)} 件は fuseneko-grid.js と一致しています。")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, svg in rendered.items():
        (OUT_DIR / f"{name}.svg").write_text(svg, encoding="utf-8")
    print(f"生成しました: {', '.join(sorted(rendered))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
