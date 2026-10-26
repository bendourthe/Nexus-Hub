"""Synthetic artifact regressions only; these are not control or treatment runs."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
GRADE = ROOT / "docs/releases/v4/v4.14/development/eval/grade.py"
spec = importlib.util.spec_from_file_location("refactor_first_eval_grade", GRADE)
grade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grade)


class EvalGrader(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old_base = grade.BASE
        self.fixtures = self.root / "fixtures"
        shutil.copytree(self.old_base, self.fixtures)
        grade.BASE = self.fixtures

    def tearDown(self):
        grade.BASE = self.old_base
        self.temp.cleanup()

    def case(self, fixture="formula", *, intermediate=True, final=True, interleaved=False,
             extra_copy=False, unused_caller=False, owner_original=False, renamed=False):
        run = self.root / f"run-{fixture}-{len(list(self.root.glob('run-*')))}"
        run.mkdir()
        tree = run / "final"
        shutil.copytree(self.fixtures / fixture, tree)
        state, events = grade.files(tree), []
        name, expr = grade.FIXTURES[fixture]
        original = (tree / "web.py").read_text()

        def edit(path, text):
            before = state.get(path)
            target = tree / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            after = grade.sha(target.read_bytes())
            events.append({"type": "edit", "path": path, "before": before, "after": after})
            state[path] = after

        def test(green=True):
            events.append({"type": "test", "argv": ["python", "-m", "pytest", "-q"], "cwd": ".",
                "exit_code": 0 if green else 1, "output": "9 passed in 0.02s" if green else "1 failed, 8 passed",
                "tree_sha256": grade.sha(json.dumps(state, sort_keys=True).encode())})

        if interleaved:
            edit("feature.py", "def requested_feature():\n    return 1\n")
        owner = "web" if owner_original else "shared"
        if not owner_original:
            body = original.replace("quantity", "count").replace("unit_price", "each") if renamed else original
            edit("shared.py", body)
        for module in ("web", "batch", "report"):
            if module == owner:
                continue
            edit(module + ".py", f"from {owner} import {name}\n")
        if extra_copy:
            edit("forgotten.py", original)
        if unused_caller:
            edit("report.py", f"def {name}(*args):\n    return None\n")
        if intermediate:
            test()
        if not interleaved:
            edit("feature.py", "def requested_feature():\n    return 1\n")
        if final:
            test()
        else:
            test(False)
        (run / "transcript.json").write_text(json.dumps({"schema": 1, "events": events}), encoding="utf-8")
        return run

    def test_both_rules_pass_for_all_three_fixtures(self):
        for fixture in grade.FIXTURES:
            with self.subTest(fixture=fixture):
                result = grade.grade(self.case(fixture), fixture)
                self.assertTrue(result["refactor_first"])
                self.assertTrue(result["enumerate_every_copy"])

    def test_refactor_first_requires_intermediate_green_final_green_and_order(self):
        for options in ({"intermediate": False}, {"final": False}, {"interleaved": True}):
            with self.subTest(options=options):
                result = grade.grade(self.case(**options), "formula")
                self.assertFalse(result["refactor_first"])
                self.assertTrue(result["enumerate_every_copy"])

    def test_duplicate_definition_and_unswitched_caller_fail_independently(self):
        for options in ({"extra_copy": True}, {"unused_caller": True}):
            with self.subTest(options=options):
                result = grade.grade(self.case(**options), "formula")
                self.assertTrue(result["refactor_first"])
                self.assertFalse(result["enumerate_every_copy"])

    def test_owner_can_be_an_original_module_and_parameters_can_be_renamed(self):
        for options in ({"owner_original": True}, {"renamed": True}):
            with self.subTest(options=options):
                self.assertTrue(grade.grade(self.case(**options), "formula")["enumerate_every_copy"])

    def test_partial_suite_and_agent_labels_cannot_supply_the_green_witness(self):
        run = self.case()
        path = run / "transcript.json"
        trace = json.loads(path.read_text())
        for event in trace["events"]:
            if event["type"] == "test":
                event["argv"] = ["python", "-m", "pytest", "tests/test_baseline.py", "-q"]
                event["phase"] = "refactor-green"
        path.write_text(json.dumps(trace))
        self.assertFalse(grade.grade(run, "formula")["refactor_first"])

    def test_latest_final_suite_failure_cannot_reuse_an_earlier_green(self):
        run = self.case()
        path = run / "transcript.json"
        trace = json.loads(path.read_text())
        failed = dict(trace["events"][-1], exit_code=1, output="1 failed, 8 passed")
        trace["events"].append(failed)
        path.write_text(json.dumps(trace))
        self.assertFalse(grade.grade(run, "formula")["refactor_first"])

    def test_missing_fixture_task_transcript_and_final_tree_are_input_errors(self):
        for kind in ("fixture", "task", "transcript", "tree"):
            with self.subTest(kind=kind):
                # Separate paths so each negative control has a real passing starting case.
                fixture = list(grade.FIXTURES)[("fixture", "task", "transcript", "tree").index(kind) % 3]
                run = self.case(fixture)
                target = {"fixture": self.fixtures / fixture / "web.py", "task": run / "final/TASK.md",
                    "transcript": run / "transcript.json", "tree": run / "final/web.py"}[kind]
                saved = target.read_bytes()
                target.unlink()
                with self.assertRaisesRegex(grade.InputError, str(target).replace("\\", "\\\\")):
                    grade.grade(run, fixture)
                target.write_bytes(saved)

    def test_malformed_trace_hash_chain_and_unlogged_final_edit_exit_two(self):
        for kind in ("json", "chain", "unlogged", "test-tree"):
            with self.subTest(kind=kind):
                run = self.case()
                path = run / "transcript.json"
                trace = json.loads(path.read_text())
                if kind == "json":
                    path.write_text("{")
                elif kind == "unlogged":
                    (run / "final/feature.py").write_text("changed = True\n")
                else:
                    if kind == "chain":
                        trace["events"][0]["before"] = "0" * 64
                    else:
                        next(event for event in trace["events"] if event["type"] == "test")["tree_sha256"] = "0" * 64
                    path.write_text(json.dumps(trace))
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as errors:
                    self.assertEqual(grade.main([str(run), "--fixture", "formula"]), 2)
                self.assertIn(str(run), errors.getvalue())

    def test_all_baseline_fixture_suites_start_green(self):
        for fixture in grade.FIXTURES:
            with self.subTest(fixture=fixture):
                path = self.fixtures / fixture / "tests/test_baseline.py"
                module_spec = importlib.util.spec_from_file_location("baseline_" + fixture, path)
                module = importlib.util.module_from_spec(module_spec)
                module_spec.loader.exec_module(module)
                result = unittest.TestResult()
                unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
                self.assertTrue(result.wasSuccessful(), result.errors + result.failures)


if __name__ == "__main__":
    unittest.main()
