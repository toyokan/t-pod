"""イベントJSONを編集した直後に validate_events.py を走らせるPostToolUseフック。

編集対象が events/ 配下または events.json のときだけ検証する。
問題がなければ何も出力しない（エージェントのコンテキストを消費しない）。
問題があるときだけ、エラー行だけを additionalContext として返す。

標準入力はUTF-8として読む。CP932で読むと日本語パスが壊れて判定できない。
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "validate_events.py"

# 検証対象とみなすパス
WATCHED_DIR = REPO_ROOT / "events"
WATCHED_FILE = REPO_ROOT / "events.json"

# エージェントへ返す最大行数
MAX_LINES = 20


def read_hook_input() -> dict:
    """標準入力のフックJSONをUTF-8で読む。"""
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def edited_path(payload: dict) -> Path | None:
    """フック入力から編集対象のパスを取り出す。"""
    tool_input = payload.get("tool_input") or {}
    raw = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not raw:
        return None
    try:
        return Path(raw).resolve()
    except OSError:
        return None


def is_watched(path: Path) -> bool:
    """検証対象のファイルかどうかを返す。"""
    if path == WATCHED_FILE:
        return True
    return path.suffix.lower() == ".json" and path.parent == WATCHED_DIR


def main() -> int:
    """エントリポイント。常に exit 0（PostToolUseは処理を止められない）。"""
    payload = read_hook_input()
    path = edited_path(payload)
    if path is None or not is_watched(path) or not VALIDATOR.exists():
        return 0

    completed = subprocess.run(
        [sys.executable, "-X", "utf8", str(VALIDATOR)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(REPO_ROOT),
        check=False,
    )
    if completed.returncode == 0:
        return 0

    output = (completed.stdout + completed.stderr).strip().splitlines()
    lines = [line for line in output if line.strip()][:MAX_LINES]
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
                        "validate_events.py がエラーを報告しました。"
                        "修正してから次へ進んでください。\n" + "\n".join(lines)
                    ),
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
