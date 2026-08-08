"""汎用 UI シェルのソースレベルの回帰テスト。"""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ShellSourceTest(unittest.TestCase):
    def test_html_does_not_contain_null_bytes(self):
        """HTML の NUL はパース時に U+FFFD へ置換されるため混入させない。"""
        source = (ROOT / "index.html").read_bytes()
        self.assertNotIn(b"\x00", source)


if __name__ == "__main__":
    unittest.main()
