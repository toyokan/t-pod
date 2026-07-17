"""イベント登録ツールの回帰テスト。"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
SPEC = importlib.util.spec_from_file_location(
    "import_event_workbook",
    ROOT / "scripts" / "import_event_workbook.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class EventWorkbookTests(unittest.TestCase):
    """入力検証と変換補助関数を確認する。"""

    def test_template_has_required_sheets(self) -> None:
        source = MODULE.EventWorkbook(ROOT / "template" / "イベント情報入力シート.xlsx")
        self.assertFalse(
            [issue for issue in source.issues if "必須シート" in issue.message],
            "v2テンプレートの必須シートが不足しています",
        )

    def test_blank_template_is_not_convertible(self) -> None:
        source = MODULE.EventWorkbook(ROOT / "template" / "イベント情報入力シート.xlsx")
        source.validate()
        self.assertTrue(any(issue.level == "ERROR" for issue in source.issues))
        self.assertTrue(any(issue.location == "基本情報.研究会名" for issue in source.issues))

    def test_cell_value_helpers(self) -> None:
        self.assertEqual(MODULE.split_lines("主催A\n\n主催B"), ["主催A", "主催B"])
        self.assertIs(MODULE.parse_bool("true"), True)
        self.assertIs(MODULE.parse_bool("false"), False)
        self.assertIsNone(MODULE.parse_bool("未定"))
        self.assertEqual(MODULE.parse_order("2"), 2)
        self.assertIsNone(MODULE.parse_order("0"))

    def test_existing_events_pass_validator(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_events.py")],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_existing_event_cannot_be_overwritten(self) -> None:
        with self.assertRaises(MODULE.WorkbookError):
            MODULE.write_outputs(
                "2026-math-summer-fes",
                {},
                {},
                {},
                "",
            )


if __name__ == "__main__":
    unittest.main()
