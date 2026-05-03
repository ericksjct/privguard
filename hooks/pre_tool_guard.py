"""Claude PreToolUse hook adapter for privguard."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from privguard.hooks import main_pre_tool


if __name__ == "__main__":
    raise SystemExit(main_pre_tool())
