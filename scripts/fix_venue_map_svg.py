#!/usr/bin/env python3
"""会場図SVG（Office書き出し）をWeb表示向けに整える。

Office 系から書き出した SVG は次の 2 点でブラウザ表示に向かない。

1. ``viewBox`` が無い。``<img class="w-full">`` で幅可変に描くため、無いと内容が
   拡縮されない解釈が起こりうる。
2. 縦書きを ``writing-mode="tb-rl"``（SVG 1.1 の古い書き方）で表現する。
   ブラウザによって字送りや括弧の向きが崩れる。

そこで ``writing-mode`` を使わず、**1 文字＝1 tspan を縦に積む**形へ機械変換する
（全算研の会場図で採った対応に揃えている）。括弧は縦書き用字形へ置換する。

使い方::

    python3 scripts/fix_venue_map_svg.py <入力.svg> <出力.svg>
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# 呼び出し側の設定に依存せず、標準出力・標準エラーをUTF-8にする。
# 日本語Windowsの既定はCP932で、-X utf8 を付け忘れると日本語が文字化けする。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# 縦書きにすると横倒しのままでは崩れて見える約物を、縦書き用字形へ置き換える
VERTICAL_FORMS = {
    "（": "︵",
    "）": "︶",
    "(": "︵",
    ")": "︶",
    "「": "﹁",
    "」": "﹂",
    "、": "︑",
    "。": "︒",
    "ー": "丨",
}

# 1 行目の基準位置。font-size 刻みで積むが、全算研SVGの実測値に合わせて少し上へ寄せる
BASELINE_OFFSET = 2.4

TB_TEXT_RE = re.compile(
    r'<text[^>]*writing-mode="tb-rl"[^>]*>(?P<body>[^<]*)</text>'
)


def add_viewbox(svg: str) -> tuple[str, str | None]:
    """``viewBox`` が無ければ宣言サイズと同値のものを足す。

    Args:
        svg: SVG の文字列。

    Returns:
        (変換後のSVG, 付与したviewBox。既にあれば None)
    """
    if "viewBox" in svg:
        return svg, None
    m = re.match(r'<svg width="(\d+(?:\.\d+)?)" height="(\d+(?:\.\d+)?)"', svg)
    if not m:
        return svg, None
    w, h = m.group(1), m.group(2)
    view_box = f"0 0 {w} {h}"
    return svg.replace(m.group(0), f'{m.group(0)} viewBox="{view_box}"', 1), view_box


def _convert_one(match: re.Match[str]) -> str:
    """``writing-mode="tb-rl"`` の text 要素を tspan 積み上げへ書き換える。"""
    tag = match.group(0)
    body = match.group("body")
    attrs = tag[: tag.index(">")]

    size_m = re.search(r'font-size="([\d.]+)"', attrs)
    if not size_m:
        return tag  # font-size が無いと行送りを決められないので触らない
    size = float(size_m.group(1))

    x_m = re.search(r'\sx="([-\d.]+)"', attrs)
    x = x_m.group(1) if x_m else "0"

    # writing-mode を外し、字送りは tspan の x/y で表現する
    attrs = re.sub(r'\s*writing-mode="[^"]*"', "", attrs)
    attrs = re.sub(r'\s+x="[-\d.]+"', "", attrs)
    attrs = re.sub(r'\s+y="[-\d.]+"', "", attrs)
    attrs += ' text-anchor="middle"'

    spans = "".join(
        f'<tspan x="{x}" y="{size * (i + 1) - BASELINE_OFFSET:.2f}">'
        f"{VERTICAL_FORMS.get(ch, ch)}</tspan>"
        for i, ch in enumerate(body)
    )
    return f"{attrs}>{spans}</text>"


def fix_svg(svg: str) -> tuple[str, str | None, int]:
    """SVG に viewBox を足し、縦書きを tspan 積み上げへ変換する。

    Args:
        svg: 変換前の SVG 文字列。

    Returns:
        (変換後のSVG, 付与したviewBox, 変換した縦書きの数)
    """
    svg, view_box = add_viewbox(svg)
    svg, count = TB_TEXT_RE.subn(_convert_one, svg)
    return svg, view_box, count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src", type=Path, help="入力SVG")
    parser.add_argument("dest", type=Path, help="出力SVG")
    args = parser.parse_args()

    svg = args.src.read_text(encoding="utf-8")
    fixed, view_box, count = fix_svg(svg)

    # 壊れたSVGを書き出さないよう、保存前にパースを通す
    import xml.etree.ElementTree as ET

    ET.fromstring(fixed)

    args.dest.write_text(fixed, encoding="utf-8", newline="")
    print(f"viewBox: {view_box or '（既にあり・変更なし）'}")
    print(f"縦書きの変換: {count} 件")
    print(f"書き出し: {args.dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
