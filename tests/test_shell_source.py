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

    def test_mascot_bubble_keeps_room_for_text(self):
        """狭い端末でもネコの幅を引いた残りを吹き出しに使い、左右余白を対称に保つ。"""
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        block = re.search(r"#mascotBubble\s*\{(.*?)\}", source, re.S)
        self.assertIsNotNone(block, "#mascotBubble の定義が見つかりません")
        css = block.group(1)
        self.assertIn("max-width: min(calc(100vw - 6rem), 19rem)", css)
        self.assertIn("padding: 4px 10px", css)
        self.assertNotRegex(css, r"max-width:\s*[^;]*52vw")

    def test_mascot_bubble_marks_title_boundaries(self):
        """短い演目名の前後を優先改行位置にし、題の語中改行を避ける。"""
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('<wbr><span class="nb">${escapeHtml(part)}</span><wbr>', source)
        self.assertRegex(source, r"#mascotBubble \.nb\s*\{[^}]*word-break:\s*keep-all")

    def test_session_links_gate_is_scoped_to_row(self):
        """運営系（admin）の links は card の外（row 直下）に置くので、ゲートは row から探す。"""
        source = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn('const linksBlock = row.querySelector(".session-links");', source)
        self.assertNotIn('card.querySelector(".session-links")', source)
        # card が無い行でもゲートが回るよう、早期 return より前に置く
        gate = source.index('const linksBlock = row.querySelector(".session-links");')
        guard = source.index("if (!card) return;")
        self.assertLess(gate, guard, "links のゲートが if (!card) return; より後ろにあります")


if __name__ == "__main__":
    unittest.main()
