"""汎用 UI シェルのソースレベルの回帰テスト。"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ShellSourceTest(unittest.TestCase):
    def test_html_does_not_contain_null_bytes(self):
        """HTML の NUL はパース時に U+FFFD へ置換されるため混入させない。"""
        source = (ROOT / "index.html").read_bytes()
        self.assertNotIn(b"\x00", source)

    def test_runtime_cache_name_matches_service_worker(self):
        """RUNTIME_CACHE はビルド工程が無いぶん 2 箇所にある。片方だけ変えると即時表示が効かなくなる。"""
        pattern = re.compile(r'RUNTIME_CACHE\s*=\s*"([^"]+)"')
        html = pattern.search((ROOT / "index.html").read_text(encoding="utf-8"))
        sw = pattern.search((ROOT / "sw.js").read_text(encoding="utf-8"))
        self.assertIsNotNone(html, "index.html に RUNTIME_CACHE の定義が見つかりません")
        self.assertIsNotNone(sw, "sw.js に RUNTIME_CACHE の定義が見つかりません")
        self.assertEqual(html.group(1), sw.group(1))

    def test_brand_surfaces_follow_brand_fg(self):
        """ブランド色のベタ塗り面に白文字を直書きしない。

        明るい brandColor（例 #FACD4B）では白文字が 1.5:1 まで落ちて WCAG AA を大きく割る。
        文字色は輝度から選ばれる --brand-fg に従わせること。
        """
        css = (ROOT / "index.html").read_text(encoding="utf-8")
        for selector in ("#appHeader", ".brand-bg", ".brand-card", ".grad-pill"):
            block = re.search(re.escape(selector) + r"\s*\{(.*?)\}", css, re.S)
            self.assertIsNotNone(block, f"{selector} の定義が見つかりません")
            self.assertNotRegex(
                block.group(1),
                r"color:\s*(#fff\b|#ffffff\b|white\b)",
                f"{selector} がブランド面の文字色を白で固定しています",
            )


if __name__ == "__main__":
    unittest.main()
