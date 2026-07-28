import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "source_audit", ROOT / "source-audit.py"
)
source_audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(source_audit)


def evidence():
    paper = (
        "10.1007/s12553-022-00719-x "
        "Creative Commons Attribution 4.0 International License "
        "study protocol "
        "Data collection is expected to be completed approximately by June 2023 "
        "64 paediatric patients use continuous glucose monitoring (CGM) systems "
        "five to fifteen minutes excerpts "
        "normal, severe hypoglycaemic or severe hyperglycaemic events"
    )
    readme = (
        "open D1NAMO dataset "
        "20 healthy subjects and 9 subjects diagnosed with Type-1 diabetes "
        "first 200 beats transformed into an image using spectrograms"
    )
    return {
        "paper-xml": paper.encode(),
        "source-readme": readme.encode(),
        "source-license": b"Apache License Version 2.0",
        "source-tree": json.dumps(
            {
                "tree": [
                    {"path": "ECG_DIABETES.docx"},
                    {"path": "ECG_DIABETES.pdf"},
                    {"path": "LICENSE"},
                    {"path": "README.md"},
                ]
            }
        ).encode(),
    }


class SourceAuditTest(unittest.TestCase):
    def test_blocks_protocol_without_executable_model(self):
        result = source_audit.audit(evidence())
        self.assertTrue(result["paperIsProspectiveProtocol"])
        self.assertEqual(result["sourceExecutableFiles"], 0)
        self.assertFalse(result["eligibleForRuntimeReview"])

    def test_requires_complete_evidence(self):
        assets = evidence()
        del assets["paper-xml"]
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)

    def test_detects_future_executable_source(self):
        assets = evidence()
        assets["source-tree"] = json.dumps(
            {
                "tree": [
                    {"path": "ECG_DIABETES.docx"},
                    {"path": "ECG_DIABETES.pdf"},
                    {"path": "LICENSE"},
                    {"path": "README.md"},
                    {"path": "model.py"},
                ]
            }
        ).encode()
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)


if __name__ == "__main__":
    unittest.main()
