import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("disabled_package_validator", ROOT / "validate.py")
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(module)


class DisabledPackageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = json.loads((ROOT / "packages.json").read_text())

    def rejects(self, mutate, verify_files=False):
        value = copy.deepcopy(self.value)
        mutate(value)
        with self.assertRaises(module.DisabledPackageError):
            module.validate(value, verify_files=verify_files)

    def test_all_six_packages_are_valid_and_bound(self):
        self.assertEqual(len(module.validate(self.value)["packages"]), 6)

    def test_rejects_inventory_or_status_change(self):
        self.rejects(lambda value: value["packages"].pop())
        self.rejects(lambda value: value["packages"][0].update(status="candidate"))

    def test_rejects_removed_blocker_or_promotion_gate(self):
        self.rejects(lambda value: value["packages"][0].update(blockers=[]))
        self.rejects(lambda value: value["packages"][0].update(promotionGate=[]))

    def test_rejects_any_runtime_registration(self):
        for key in module.EXECUTION_KEYS:
            self.rejects(lambda value, key=key: value["packages"][0]["execution"].update({key: True}))

    def test_rejects_missing_or_stale_evidence_binding(self):
        self.rejects(lambda value: value["packages"][0].update(evidenceBindings=[]))
        self.rejects(
            lambda value: value["packages"][0]["evidenceBindings"][0].update(sha256="f" * 64),
            verify_files=True,
        )

    def test_rejects_empty_source_or_study_text(self):
        self.rejects(lambda value: value["packages"][0]["primarySources"][0].update(license=""))
        self.rejects(lambda value: value["packages"][0]["proposedStudy"].update(reference=""))


if __name__ == "__main__":
    unittest.main()
