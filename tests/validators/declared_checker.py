"""Run the checker with fixture member declarations (test-only subprocess wrapper).

The production checker reads its member rules from `completion_minor.MEMBER_DECLARATIONS`.
A test fixture plan has its own path and hash, so this wrapper swaps in the version-prefix
table from `member_declarations` and then runs the real checker script unchanged.
"""
import runpy
import sys
from pathlib import Path

scripts = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(scripts))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import completion_minor
import member_declarations

member_declarations.apply_to(completion_minor)
checker = scripts / "check_plan_completion.py"
sys.argv[0] = str(checker)
runpy.run_path(str(checker), run_name="__main__")
