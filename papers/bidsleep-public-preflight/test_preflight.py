import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("bidsleep_preflight", ROOT / "preflight.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(module)


class BidsleepPreflightTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preflight = json.loads((ROOT / "preflight.json").read_text())
        cls.fixture = json.loads((ROOT / "generated-metadata.json").read_text())

    def test_generated_metadata_smoke_is_subject_separated(self):
        report = module.smoke(self.preflight, self.fixture)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["splitCounts"], {"train": 3, "validation": 1, "test": 1})
        self.assertFalse(report["brainstemExecutionEnabled"])

    def test_rejects_duplicate_subjects(self):
        fixture = copy.deepcopy(self.fixture)
        fixture["subjects"][1]["id"] = fixture["subjects"][0]["id"]
        with self.assertRaises(module.PreflightError):
            module.smoke(self.preflight, fixture)

    def test_rejects_runtime_or_catalogue_enablement(self):
        for key in ("brainstemExecutionEnabled", "catalogueEntryEnabled"):
            preflight = copy.deepcopy(self.preflight)
            preflight["controls"][key] = True
            with self.assertRaises(module.PreflightError):
                module.validate_preflight(preflight)

    def test_rejects_slice_12_gate_bypass(self):
        preflight = copy.deepcopy(self.preflight)
        preflight["slice12Gate"]["decision"] = "approved"
        with self.assertRaises(module.PreflightError):
            module.validate_preflight(preflight)


if __name__ == "__main__":
    unittest.main()
