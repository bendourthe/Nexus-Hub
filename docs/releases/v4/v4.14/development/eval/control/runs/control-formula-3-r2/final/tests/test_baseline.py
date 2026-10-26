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
            for row in [[2,3,8],[0,10,2],[-2,3,-4]]:
                with self.subTest(module=name, row=row):
                    self.assertEqual(module.total(*row[:-1]), row[-1])
