#!/usr/bin/env python3
"""次回イベントバナーを配信向けに軽量化する。

会場の細い回線で開かれる前提のサイト（README 参照）なので、告知バナーのような
大きな画像は「表示枠に必要なだけ」の解像度に落としてから配信する。

対象と方針は TARGETS で宣言する。生成物はリポジトリにコミットするので
（`build_fuseneko.py` と同じ作法）、元画像を差し替えたらこのスクリプトを
実行し直すこと。

  python3 scripts/optimize_images.py           # 生成して差分を報告
  python3 scripts/optimize_images.py --check   # 生成せず、要更新かどうかだけ見る（CI 向け）

なぜ 2 通りの出力先があるか:
  - webp: 現行イベント。JSON の image を .webp に向けられるので最小サイズを取れる。
  - png : 終了済みイベント。JSON を編集しない規約（CLAUDE.md）なので、
          ファイル名と拡張子を保ったまま中身だけ軽くする。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ModuleNotFoundError as exc:  # pragma: no cover - 実行環境の問題
    raise SystemExit(
        "Pillow が必要です。python -m pip install -r requirements-tools.txt を実行してください。"
    ) from exc

try:  # Windows の cp932 端末でも UTF-8 で出力する
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]

# 表示枠は index.html の `w-full max-h-72 object-cover`。本文の最大幅が 672px なので
# DPR3 でも 2016px あれば足りるが、バナーは object-cover で上下が切られる帯であり、
# 実際に見えるのは横 672px ぶん。1400px あれば DPR2 で等倍、DPR3 でも粗さは出ない。
MAX_WIDTH = 1400

TARGETS = (
    # (元画像, 出力先, 形式, 品質)
    # 全算研2026（開催中）: JSON の nextEvent.image を .webp に向けている
    (
        "assets/next-event-2026-zensanken-37.png",
        "assets/next-event-2026-zensanken-37.webp",
        "WEBP",
        82,
    ),
    # 算数サマーフェス2026（終了済み）: JSON を触らない規約なので同名 PNG を上書きする
    (
        "assets/next-event-2026-math-summer-fes.png",
        "assets/next-event-2026-math-summer-fes.png",
        "PNG",
        None,
    ),
)


def _load_rgb(path: Path) -> Image.Image:
    """元画像を RGB で開く（バナーに透過は無い前提。あっても白で合成する）。"""
    img = Image.open(path)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        flat = Image.new("RGB", img.size, (255, 255, 255))
        flat.paste(img, mask=img.split()[-1])
        return flat
    return img.convert("RGB")


def _resized(img: Image.Image, max_width: int) -> Image.Image:
    """必要なときだけ縮小する（元が小さければ拡大しない）。"""
    if img.width <= max_width:
        return img
    height = round(img.height * max_width / img.width)
    return img.resize((max_width, height), Image.LANCZOS)


def _save(img: Image.Image, dest: Path, fmt: str, quality: int | None) -> bytes:
    """指定形式でエンコードしたバイト列を返す（まだ書かない）。"""
    import io

    buf = io.BytesIO()
    if fmt == "WEBP":
        # method=6 は最も遅いが最も小さい。生成は手元で一度きりなので速度は問わない。
        img.save(buf, "WEBP", quality=quality, method=6)
    else:
        # PNG-24 のままだとグラデーションで巨大化する（縮小だけでは 1MB 級が残る）。
        # 256 色へ量子化＋誤差拡散すると 1/3 になり、バナー程度の絵柄では
        # 帯も文字のフチも目視で判別できない（実測して確認済み）。
        pal = img.quantize(colors=256, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG)
        pal.save(buf, "PNG", optimize=True, compress_level=9)
    return buf.getvalue()


def process(check_only: bool) -> int:
    """TARGETS を処理し、更新が要る（あった）件数を返す。"""
    changed = 0
    for src_rel, dest_rel, fmt, quality in TARGETS:
        src = ROOT / src_rel
        dest = ROOT / dest_rel
        if not src.exists():
            print(f"スキップ（元画像が無い）: {src_rel}")
            continue

        before = src.stat().st_size
        with _load_rgb(src) as img:
            out = _save(_resized(img, MAX_WIDTH), dest, fmt, quality)

        # 上書き対象（PNG）で既に十分小さいなら触らない。再実行で無駄な差分を作らない。
        if dest.exists() and len(out) >= dest.stat().st_size:
            print(f"変更なし: {dest_rel}（{dest.stat().st_size:,} B）")
            continue

        changed += 1
        pct = 100 - len(out) * 100 // before
        if check_only:
            print(f"要更新: {dest_rel}（{before:,} B → {len(out):,} B / -{pct}%）")
        else:
            dest.write_bytes(out)
            print(f"生成: {src_rel} → {dest_rel}（{before:,} B → {len(out):,} B / -{pct}%）")
    return changed


def main() -> int:
    """コマンドライン入口。--check のときは要更新があれば exit 1。"""
    parser = argparse.ArgumentParser(description="次回イベントバナーを軽量化する")
    parser.add_argument(
        "--check", action="store_true", help="生成せず、要更新かどうかだけ判定する"
    )
    args = parser.parse_args()
    changed = process(args.check)
    if args.check and changed:
        print("最適化されていない画像があります。python3 scripts/optimize_images.py を実行してください。")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
