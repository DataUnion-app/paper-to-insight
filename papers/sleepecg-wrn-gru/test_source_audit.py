import importlib.util
import io
import json
import tarfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("source_audit", ROOT / "source-audit.py")
source_audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(source_audit)


def evidence():
    model_buffer = io.BytesIO()
    with zipfile.ZipFile(model_buffer, "w") as archive:
        archive.writestr(
            "info.yml",
            "hrv-time hrv-frequency recording_start_time age gender "
            "stages_mode: wake-rem-nrem",
        )
    source_audit.MODEL_SHA256 = source_audit.hashlib.sha256(
        model_buffer.getvalue()
    ).hexdigest()

    archive_buffer = io.BytesIO()
    with tarfile.open(fileobj=archive_buffer, mode="w:gz") as archive:
        files = {
            "x/PKG-INFO": (
                "Name: sleepecg Version: 0.5.9 License: BSD 3-Clause "
                "10.21105/joss.05411"
            ),
            "x/LICENSE": "BSD 3-Clause License",
            "x/docs/classification.md": (
                "`wrn-gru-mesa` MESA (1971) SHHS (1000) |0.75|0.54| "
                "limited performance in WAKE–REM–NREM classification"
            ),
            "x/examples/classifiers/wrn_gru_mesa.py": (
                'read_mesa read_shhs "recording_start_time" "age" "gender" '
                'stages_mode = "wake-rem-nrem"'
            ),
        }
        for name, text in files.items():
            data = text.encode()
            member = tarfile.TarInfo(name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
        data = model_buffer.getvalue()
        member = tarfile.TarInfo("x/src/sleepecg/classifiers/wrn-gru-mesa.zip")
        member.size = len(data)
        archive.addfile(member, io.BytesIO(data))

    records = [f"slp{i:02d}" for i in range(18)]
    checksums = "\n".join(
        f"{'0' * 64} {record}.{extension}"
        for record in records
        for extension in ("hea", "ecg", "st")
    )
    return {
        "sleepecg-sdist": archive_buffer.getvalue(),
        "slpdb-records": ("\n".join(records) + "\n").encode(),
        "slpdb-checksums": checksums.encode(),
    }


class SourceAuditTest(unittest.TestCase):
    def test_accepts_exact_open_artifact_contract(self):
        result = source_audit.audit(evidence())
        self.assertEqual(result["modelStagesMode"], "wake-rem-nrem")
        self.assertEqual(result["slpdbAnnotationFilesPinned"], 54)
        self.assertFalse(result["eligibleForRuntimeReview"])

    def test_rejects_incomplete_dataset_manifest(self):
        assets = evidence()
        lines = assets["slpdb-checksums"].decode().splitlines()
        assets["slpdb-checksums"] = "\n".join(lines[:-1]).encode()
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)

    def test_rejects_changed_model(self):
        assets = evidence()
        source_audit.MODEL_SHA256 = "0" * 64
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)


if __name__ == "__main__":
    unittest.main()

