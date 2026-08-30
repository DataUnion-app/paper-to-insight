import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock


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

    def test_rejects_personalized_clock_or_reported_variant_claim(self):
        for key in ("personalizedClockReproducible", "reportedBidsleepVariantKnown"):
            preflight = copy.deepcopy(self.preflight)
            preflight["timeReference"][key] = True
            with self.assertRaises(module.PreflightError):
                module.validate_preflight(preflight)

    def test_rejects_time_formula_drift(self):
        preflight = copy.deepcopy(self.preflight)
        preflight["timeReference"]["cosineFormula"] = "cos(seconds_since_start)"
        with self.assertRaises(module.PreflightError):
            module.validate_preflight(preflight)

    def test_rejects_published_experiment_or_architecture_drift(self):
        mutations = [
            ("experiment", "splitSubjects", {"train": 29, "validation": 9, "test": 9}),
            ("experiment", "crossValidationFolds", 10),
            ("architectureEvidence", "variantResolved", True),
        ]
        for section, key, value in mutations:
            preflight = copy.deepcopy(self.preflight)
            preflight["paper"][section][key] = value
            with self.assertRaises(module.PreflightError):
                module.validate_preflight(preflight)

    @staticmethod
    def public_entries():
        entries = {}
        for subject in range(47):
            nights = 6 if subject < 18 else 5
            for night in range(1, nights + 1):
                for name in module.NIGHT_FILES:
                    path = f"Bidslab{subject:02d}/{night}/{name}"
                    entries[path] = hashlib.sha256(path.encode()).hexdigest()
        return entries

    def test_public_plan_is_exhaustive_and_subject_separated(self):
        plan = module.assemble_public_plan(self.preflight, self.public_entries())
        self.assertEqual(plan["counts"], {"subjects": 47, "nights": 253, "files": 759})
        self.assertEqual(
            {name: len(value["subjects"]) for name, value in plan["partitions"].items()},
            {"train": 31, "validation": 5, "test": 11},
        )
        self.assertEqual(plan["schema"], "paper-to-insight.bidsleep-public-plan/v2")
        self.assertEqual(plan["assignment"]["status"], "reconstructed_from_published_counts")
        self.assertFalse(plan["assignment"]["publishedSubjectIdentitiesAvailable"])
        self.assertEqual(plan["publishedExperiment"]["training"]["optimizationEpochs"], 500)
        self.assertFalse(plan["modelEvidence"]["variantResolved"])
        self.assertIn(plan["benchmark"]["night"], plan["partitions"]["train"]["nights"])
        self.assertEqual(set(plan["benchmark"]["files"]), module.NIGHT_FILES)
        self.assertEqual(
            plan["controls"],
            {
                "signalFilesDownloaded": False,
                "downloadApproved": False,
                "modelVariantSelected": False,
                "brainstemExecutionEnabled": False,
            },
        )

    def test_rejects_bad_manifest_and_incomplete_night(self):
        digest = "0" * 64
        with self.assertRaises(module.PreflightError):
            module.parse_signal_manifest(f"bad  Bidslab00/1/hr.csv\n".encode())
        with self.assertRaises(module.PreflightError):
            module.parse_signal_manifest(
                f"{digest}  Bidslab00/1/hr.csv\n{digest}  Bidslab00/1/hr.csv\n".encode()
            )
        entries = self.public_entries()
        entries.pop("Bidslab00/1/hr.csv")
        with self.assertRaises(module.PreflightError):
            module.assemble_public_plan(self.preflight, entries)

    def test_source_availability_guard(self):
        revision = self.preflight["source"]["revision"]

        def responses(head=revision, releases=None):
            def fetch(url, limit=5_000_000):
                value = {"sha": head} if url.endswith("/commits/main") else (releases or [])
                return json.dumps(value).encode()
            return fetch

        with mock.patch.object(module, "fetch_small", responses()):
            self.assertEqual(
                module.verify_source_availability(self.preflight["source"]),
                {"status": "passed", "mainHead": revision, "releaseCount": 0},
            )
        for fetch in (responses(head="0" * 40), responses(releases=[{"tag_name": "v1"}])):
            with mock.patch.object(module, "fetch_small", fetch):
                with self.assertRaises(module.PreflightError):
                    module.verify_source_availability(self.preflight["source"])


if __name__ == "__main__":
    unittest.main()
