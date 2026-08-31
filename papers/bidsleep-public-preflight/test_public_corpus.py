#!/usr/bin/env python3

import hashlib
import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("bidsleep_public_corpus", ROOT / "public_corpus.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PublicCorpusTest(unittest.TestCase):
    def test_extracts_only_hash_verified_signal_files(self):
        files = {
            "Bidslab00/1/hr.csv": b"hr",
            "Bidslab00/1/labels.mat": b"labels",
            "Bidslab00/1/motion.csv": b"motion",
        }
        entries = {name: hashlib.sha256(body).hexdigest() for name, body in files.items()}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "public.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                for name, body in files.items():
                    archive.writestr(f"dataset-1.0.0/{name}", body)
                archive.writestr("dataset-1.0.0/README.txt", "public")
            result = MODULE.extract_verified(archive_path, entries, root / "raw", 100)
            self.assertEqual(result["files"], 3)
            self.assertEqual(result["extractedBytes"], sum(map(len, files.values())))
            for name, digest in entries.items():
                self.assertEqual(MODULE.sha256(root / "raw" / name), digest)

    def test_rejects_path_escape_and_symlink(self):
        with self.assertRaisesRegex(ValueError, "unsafe ZIP member"):
            MODULE.signal_member_name("../Bidslab00/1/hr.csv", {"Bidslab00/1/hr.csv"})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "public.zip"
            info = zipfile.ZipInfo("Bidslab00/1/hr.csv")
            info.external_attr = 0o120777 << 16
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(info, "target")
            digest = hashlib.sha256(b"target").hexdigest()
            with self.assertRaisesRegex(ValueError, "symlink"):
                MODULE.extract_verified(
                    archive_path, {"Bidslab00/1/hr.csv": digest}, root / "raw", 100
                )

    def test_existing_hash_mismatch_fails_closed(self):
        body = b"expected"
        name = "Bidslab00/1/hr.csv"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "public.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(name, body)
            target = root / "raw" / name
            target.parent.mkdir(parents=True)
            target.write_bytes(b"different")
            with self.assertRaisesRegex(ValueError, "existing extracted file hash differs"):
                MODULE.extract_verified(
                    archive_path,
                    {name: hashlib.sha256(body).hexdigest()},
                    root / "raw",
                    100,
                )

    def test_rejects_preexisting_destination_symlink(self):
        body = b"expected"
        name = "Bidslab00/1/hr.csv"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "public.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(name, body)
            raw = root / "raw"
            raw.mkdir()
            (raw / "Bidslab00").symlink_to(root / "outside", target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "contains a symlink"):
                MODULE.extract_verified(
                    archive_path,
                    {name: hashlib.sha256(body).hexdigest()},
                    raw,
                    100,
                )


if __name__ == "__main__":
    unittest.main()
