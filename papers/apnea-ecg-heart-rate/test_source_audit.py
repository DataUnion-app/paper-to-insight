import importlib.util
import io
import json
import tarfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("source_audit", ROOT / "source-audit.py")
source_audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(source_audit)


def source_archive() -> bytes:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        for name in sorted(source_audit.EXECUTABLES):
            body = (
                "GNU General Public License\nFree Software Foundation\n"
                "either version 2 of the License, or (at your option) any later\n"
            )
            if name.endswith("get_apdet"):
                body += "\n".join(source_audit.METHOD_MARKERS)
            data = body.encode()
            member = tarfile.TarInfo(name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
    return stream.getvalue()


def evidence():
    return {
        "apdet-source": source_archive(),
        "apnea-ecg-manifest": b"00 a01.apn\n",
        "apnea-ecg-paper": b"paper",
        "apnea-ecg-records": "\n".join([f"a{i:02d}" for i in range(1, 36)] + [f"x{i:02d}" for i in range(1, 36)]).encode(),
        "method-paper": b"method",
        "ucddb-manifest": b"00 ucddb002_respevt.txt\n",
        "ucddb-records": "\n".join(["ucddb002.rec", "ucddb003.rec"] + [f"ucddb{i:03d}.rec" for i in range(4, 27)]).encode(),
    }


class SourceAuditTest(unittest.TestCase):
    def test_freezes_official_method_and_fails_closed(self):
        result = source_audit.audit(evidence())
        self.assertTrue(result["methodConstantsVerified"])
        self.assertTrue(result["licenceReviewRequiredBeforeRedistribution"])
        self.assertFalse(result["personalApneaOutputEnabled"])

    def test_rejects_missing_method_constant(self):
        assets = evidence()
        source_audit.METHOD_MARKERS += ("missing-marker",)
        with self.assertRaises(source_audit.AuditError):
            source_audit.audit(assets)


if __name__ == "__main__":
    unittest.main()
