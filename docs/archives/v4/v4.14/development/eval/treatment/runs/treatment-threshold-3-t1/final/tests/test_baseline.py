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
            for row in [[9,False],[10,True],[11,True]]:
                with self.subTest(module=name, row=row):
                    self.assertEqual(module.reached(*row[:-1]), row[-1])
