"""ふせんネコのグリッドと生成 SVG の検査。

造形の定義は assets/fuseneko/fuseneko-grid.js の 1 箇所だけで、SVG 資産は
scripts/build_fuseneko.py がそこから生成する。ここでは
「グリッドが 24×24 に収まっているか」と「生成物がずれていないか」を見張る。
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_fuseneko import (  # noqa: E402
    GRID,
    GRID_JS,
    OUT_DIR,
    SVG_TARGETS,
    apply_patches,
    parse_grid_js,
    render,
    validate,
)


class FusenekoGridTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parsed = parse_grid_js(GRID_JS.read_text(encoding="utf-8"))
        cls.base = cls.parsed["arrays"]["FUSENEKO_BASE"]

    def test_grid_is_well_formed(self):
        """24 行 × 24 文字、未定義の文字なし。"""
        self.assertEqual(validate(self.parsed), [])

    def test_expected_patches_exist(self):
        """書式が変わってパッチを拾えなくなったら気づけるようにする。"""
        expected = {
            "FN_SMILE",
            "FN_SERIOUS",
            "FN_BLINK",
            "FN_SURPRISE",
            "FN_YAWN",
            "FN_LOOK_R",
            "FN_LOOK_L",
            "FN_LOOK_UP",
            "FN_EARS_DOWN",
            "FN_SPARK_A",
            "FN_SPARK_B",
            "FUSENEKO_TAIL",
        }
        self.assertLessEqual(expected, set(self.parsed["patches"]))

    def test_patches_stay_inside_the_grid(self):
        """どのパッチを重ねても 24×24 からはみ出さない。"""
        for name, patch in self.parsed["patches"].items():
            rows = apply_patches(self.base, [patch])
            self.assertEqual(len(rows), GRID, name)
            for i, row in enumerate(rows):
                self.assertEqual(len(row), GRID, f"{name} row {i}")

    def test_body_is_a_clean_rectangle(self):
        """胴体の下辺は水平・左右は垂直で、下の角は四角のまま。

        折れ角は右上だけの造形なので、ここが崩れていたらシルエットの取り違え。
        """
        left, right, bottom = 1, 17, 19
        for row in range(11, bottom):  # 折れ角より下だけを見る
            self.assertEqual(self.base[row][left], "K", f"row {row} の左辺")
            self.assertEqual(self.base[row][right], "K", f"row {row} の右辺")
        self.assertEqual(self.base[bottom][left : right + 1], "K" * (right - left + 1))

    def test_cheeks_do_not_touch_the_outline(self):
        """ほっぺは輪郭に接触させない（設定資料の決めごと）。"""
        for row_index, row in enumerate(self.base):
            for col, ch in enumerate(row):
                if ch != "P":
                    continue
                self.assertNotIn("K", (row[col - 1], row[col + 1]),
                                 f"row {row_index} col {col} のほっぺが輪郭に接触している")

    def test_every_expression_keeps_the_nose(self):
        """どの表情でも鼻（col 9 / row 14）を塗り潰さない。

        口を差し替えるパッチで rows 14 をまとめて上書きすると鼻ごと消え、
        猫の顔に見えなくなる。表情を足すたびに踏みやすいのでここで止める。
        """
        nose_col, nose_row = 9, 14
        for name, patch in self.parsed["patches"].items():
            if name in {"FUSENEKO_TAIL"}:  # しっぽは顔に触れない
                continue
            rows = apply_patches(self.base, [patch])
            self.assertEqual(
                rows[nose_row][nose_col],
                "E",
                f"{name} が鼻（col {nose_col} / row {nose_row}）を消している",
            )

    def test_committed_svgs_match_the_grid(self):
        """生成物が fuseneko-grid.js とずれていないか。

        ずれていたら `python3 scripts/build_fuseneko.py` で作り直す。
        """
        rendered = render(self.parsed)
        self.assertEqual(set(rendered), set(SVG_TARGETS))
        for name, svg in rendered.items():
            path = OUT_DIR / f"{name}.svg"
            self.assertTrue(path.exists(), f"{path} が無い")
            self.assertEqual(
                path.read_text(encoding="utf-8"),
                svg,
                f"{path.name} が古い。python3 scripts/build_fuseneko.py で再生成すること",
            )


if __name__ == "__main__":
    unittest.main()
