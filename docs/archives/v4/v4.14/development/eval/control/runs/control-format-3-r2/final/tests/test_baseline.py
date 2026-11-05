"""Existing public behavior; run with python -m pytest -q from the fixture root."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ExistingBehavior(unittest.TestCase):
    def test_all_three_public_modules(self):
        for name in ("web", "batch", "report"):
            spec = importlib.util.spec_from_file_location("subject_" + name, ROOT / (name + ".py"))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for row in [["A",1.2,"A: 1.20"],["A,B",2,"A,B: 2.00"],["negative",-1.25,"negative: -1.25"]]:
                with self.subTest(module=name, row=row):
                    self.assertEqual(module.display(*row[:-1]), row[-1])
