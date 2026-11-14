"""Run any installed script with fixture member declarations (test-only subprocess wrapper).

    declared_script.py <script-name> [args...]

`<script-name>` is a file under `scripts/` such as `minor_close.py`. The wrapper swaps in the
version-prefix table from `member_declarations`, then runs that script unchanged, for scripts
that load a v4.15 run record without going through `check_plan_completion.py`.
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
target = scripts / sys.argv[1]
sys.argv = [str(target), *sys.argv[2:]]
runpy.run_path(str(target), run_name="__main__")
