"""Deterministic artifact grader; never invokes a model, shell, or the submitted code."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

FIXTURES = {
    "formula": ("total", "quantity * unit_price + 2"),
    "format": ("display", 'f"{name}: {value:.2f}"'),
    "threshold": ("reached", "value >= 10"),
}
BASE = Path(__file__).resolve().parent / "fixtures"


class InputError(ValueError):
    """An absent or malformed artifact is not a failing measured run."""


def read(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise InputError(f"missing or nonregular input: {path}")
    return path.read_bytes()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def files(root: Path) -> dict[str, str]:
    if not root.is_dir() or root.is_symlink():
        raise InputError(f"missing tree: {root}")
    result = {}
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root)
        if any(part.startswith(".") or part == "__pycache__" for part in rel.parts):
            continue
        if not path.resolve().is_relative_to(root.resolve()):
            raise InputError(f"tree path escapes fixture: {path}")
        result[rel.as_posix()] = sha(read(path))
    return result


def symbol(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = symbol(node.value)
        return f"{parent}.{node.attr}" if parent else None
    return None


def expression_key(node: ast.AST) -> str:
    """Normalize identifier spelling and commutative arithmetic, not arbitrary algebra."""
    names = {}

    class Shape(ast.NodeTransformer):
        def visit_Name(self, part):
            names.setdefault(part.id, f"name{len(names)}")
            return ast.Name(id=names[part.id], ctx=ast.Load())

        def visit_BinOp(self, part):
            part = self.generic_visit(part)
            if isinstance(part.op, (ast.Add, ast.Mult)):
                if ast.dump(part.left) > ast.dump(part.right):
                    part.left, part.right = part.right, part.left
            return part

    return ast.dump(Shape().visit(copy.deepcopy(node)), include_attributes=False)


def enumerate_copies(root: Path, name: str, expression: str) -> tuple[bool, dict]:
    expected = expression_key(ast.parse(expression, mode="eval").body)
    definitions, functions, imports = [], {}, {}
    for rel in files(root):
        path = root / rel
        if any(part == "tests" for part in Path(rel).parts) or Path(rel).name.startswith("test_"):
            continue
        module = Path(rel).with_suffix("").as_posix().replace("/", ".")
        try:
            tree = ast.parse(read(path), filename=str(path))
        except SyntaxError:
            return False, {"reason": "production syntax error", "path": rel}
        aliases = {}
        for node in tree.body:
            if isinstance(node, ast.Import):
                for item in node.names:
                    aliases[item.asname or item.name.split(".")[0]] = item.name if item.asname else item.name.split(".")[0]
            elif isinstance(node, ast.ImportFrom):
                package = module.split(".")[:-1]
                prefix = package[:len(package) - node.level + 1] if node.level else []
                target = ".".join([*prefix, *([node.module] if node.module else [])])
                for item in node.names:
                    aliases[item.asname or item.name] = f"{target}.{item.name}"
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                key = f"{module}.{node.name}"
                functions[key] = node
                for part in ast.walk(node):
                    if expression_key(part) == expected:
                        definitions.append(key)
        imports[module] = aliases
    if len(definitions) != 1:
        return False, {"definitions": definitions, "reason": "expected exactly one expression definition"}
    owner = definitions[0]

    def resolve(module, dotted):
        first, _, rest = dotted.partition(".")
        return imports.get(module, {}).get(first, f"{module}.{first}") + ("." + rest if rest else "")

    def reaches(key, seen):
        if key == owner:
            return True
        if key in seen or key not in functions:
            return False
        module = key.rsplit(".", 1)[0]
        return any(reaches(resolve(module, dotted), seen | {key})
                   for node in ast.walk(functions[key]) if isinstance(node, ast.Call)
                   if (dotted := symbol(node.func)))

    callers = {}
    for module in ("web", "batch", "report"):
        key = f"{module}.{name}"
        if key not in functions:
            key = imports.get(module, {}).get(name, key)
        callers[module] = reaches(key, set())
    return all(callers.values()), {"definitions": definitions, "original_callers": callers}


def temporal(run: Path, baseline: dict[str, str], final: dict[str, str]) -> tuple[bool, dict]:
    trace_path = run / "transcript.json"
    try:
        trace = json.loads(read(trace_path))
    except (ValueError, UnicodeError) as error:
        raise InputError(f"malformed transcript: {trace_path}: {error}") from error
    if not isinstance(trace, dict) or trace.get("schema") != 1 or not isinstance(trace.get("events"), list):
        raise InputError(f"malformed transcript: {trace_path}")
    state = dict(baseline)
    refactors, features, greens, edits, suite_results = [], [], [], [], []
    for index, event in enumerate(trace["events"]):
        if not isinstance(event, dict):
            raise InputError(f"malformed event {index}: {trace_path}")
        if event.get("type") == "edit":
            path = event.get("path")
            if (not isinstance(path, str) or not path.endswith(".py") or "\\" in path
                    or Path(path).is_absolute() or any(p in {"", ".", ".."} for p in path.split("/"))):
                raise InputError(f"invalid edit path at event {index}: {trace_path}")
            before, after = event.get("before"), event.get("after")
            if before != state.get(path) or (after is not None and not re.fullmatch("[a-f0-9]{64}", str(after))):
                raise InputError(f"broken edit hash chain at event {index}: {trace_path}")
            if after is None:
                state.pop(path, None)
            else:
                state[path] = after
            if before == after:
                continue
            edits.append(index)
            (features if path == "feature.py" or path.startswith("tests/") or Path(path).name.startswith("test_") else refactors).append(index)
        elif event.get("type") == "test":
            argv = event.get("argv")
            output = event.get("output")
            if (not isinstance(argv, list) or not argv or not all(isinstance(arg, str) for arg in argv)
                    or not isinstance(event.get("cwd"), str)
                    or type(event.get("exit_code")) is not int or not isinstance(output, str)
                    or event.get("tree_sha256") != sha(json.dumps(state, sort_keys=True).encode())):
                raise InputError(f"malformed or unbound full-suite result at event {index}: {trace_path}")
            full_suite = argv == ["python", "-m", "pytest", "-q"] and event["cwd"] == "."
            if (full_suite and event["exit_code"] == 0 and re.search(r"\b[1-9][0-9]* passed\b", output)
                    and not re.search(r"\b(?:[1-9][0-9]* (?:failed|errors?)|ERROR|FAILED)\b", output)):
                greens.append(index)
            if full_suite:
                suite_results.append((index, index in greens))
        else:
            raise InputError(f"unsupported event {index}: {trace_path}")
    if state != final:
        raise InputError(f"final tree differs from recorded edit chain: {run / 'final'}")
    between = bool(refactors and features and any(max(refactors) < i < min(features) for i in greens))
    final_green = bool(edits and suite_results and suite_results[-1][1] and suite_results[-1][0] > max(edits))
    return between and final_green, {"refactor_edits": refactors, "feature_edits": features,
                                    "green_full_suite_results": greens, "final_suite_green": final_green}


def grade(run: Path, fixture: str) -> dict:
    baseline = BASE / fixture
    if fixture not in FIXTURES:
        raise InputError(f"unknown fixture: {baseline}")
    read(Path(__file__).resolve().parent / "task.md")
    read(baseline / "TASK.md")
    read(baseline / "tests" / "test_baseline.py")
    read(run / "final" / "tests" / "test_baseline.py")
    for module in ("web", "batch", "report"):
        read(baseline / f"{module}.py")
        read(run / "final" / f"{module}.py")
    read(run / "final" / "TASK.md")
    initial, final = files(baseline), files(run / "final")
    refactor, timeline = temporal(run, initial, final)
    every_copy, copies = enumerate_copies(run / "final", *FIXTURES[fixture])
    return {"fixture": fixture, "refactor_first": refactor, "enumerate_every_copy": every_copy,
            "timeline": timeline, "copies": copies}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--fixture", choices=tuple(FIXTURES), required=True)
    args = parser.parse_args(argv)
    try:
        result = grade(args.run, args.fixture)
    except (InputError, OSError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0 if result["refactor_first"] and result["enumerate_every_copy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
