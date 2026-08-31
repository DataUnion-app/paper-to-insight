import importlib.util
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy.io import savemat


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("bidsleep_converter", ROOT / "converter.py")
converter = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(converter)


def write_night(path: Path, epochs: int, *, short_hr=False) -> None:
    start = 1_700_000_000.0
    end = epochs * 30
    first = 1 if short_hr else 0
    hr_times = list(range(first, end, 5))
    if not short_hr and hr_times[-1] != end - 1:
        hr_times.append(end - 1)
    with (path / "hr.csv").open("w") as handle:
        handle.write("timestamp,hr\n")
        for offset in hr_times:
            handle.write(f"{start + offset},{60 + offset / 100}\n")
    with (path / "motion.csv").open("w") as handle:
        handle.write("timestamp,x,y,z\n")
        for offset in range(end):
            handle.write(f"{start + offset},3,4,0\n")
    labels = np.arange(epochs, dtype=np.uint8) % 6
    savemat(
        path / "labels.mat",
        {"recStart": np.asarray([[start]]), "dreem_label": labels, "expert_label": labels},
    )
    with (path / "labels.mat").open("r+b") as handle:
        header = b"MATLAB 5.0 MAT-file, Platform: generated BIDSleep converter proof"
        handle.write(header.ljust(116, b" "))


class ConverterTest(unittest.TestCase):
    def test_generated_night_is_aligned_and_deterministic(self):
        with tempfile.TemporaryDirectory() as folder:
            night = Path(folder)
            write_night(night, 4)
            hr = converter.read_csv(night / "hr.csv", 2, converter.HR_HEADERS)
            motion = converter.read_csv(night / "motion.csv", 4, converter.MOTION_HEADERS)
            start, dreem, expert = converter.load_labels(night / "labels.mat")
            arrays = converter.convert_arrays(
                hr, motion, start, dreem, expert, minimum_epochs=4, maximum_epochs=4
            )
            self.assertEqual(arrays["signal_1hz"].shape, (120, 2))
            np.testing.assert_allclose(arrays["signal_1hz"][:, 1], 5)
            np.testing.assert_array_equal(arrays["stage_four"], [0, 1, 1, 2])
            np.testing.assert_array_equal(arrays["stage_mask"], [True] * 4)
            self.assertEqual(arrays["epoch_freq_hr_stats"].shape, (4, 3))
            self.assertEqual(arrays["epoch_time_candidates"].shape, (4, 2))
            np.testing.assert_allclose(
                arrays["epoch_time_candidates"][:, 1], np.arange(4) * 30 / 3600
            )
            self.assertAlmostEqual(
                float(arrays["epoch_time_candidates"][0, 0]),
                -math.cos((-5 * 3600) * 2 * math.pi / (24 * 3600)),
            )
            first = night / "first.npz"
            second = night / "second.npz"
            converter.write_npz(first, arrays)
            converter.write_npz(second, arrays)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_outliers_are_removed_before_interpolation(self):
        start = 1_700_000_000.0
        offsets = np.arange(30, dtype=np.float64)
        hr = np.column_stack((start + offsets, np.full(30, 60.0)))
        motion = np.column_stack((start + offsets, np.ones(30), np.zeros((30, 2))))
        hr[15, 1] = 600
        motion[15, 1] = 100
        labels = np.asarray([0], dtype=np.uint8)
        arrays = converter.convert_arrays(
            hr, motion, start, labels, labels, minimum_epochs=1, maximum_epochs=1
        )
        self.assertEqual(float(arrays["signal_1hz"][15, 0]), 60)
        self.assertEqual(float(arrays["signal_1hz"][15, 1]), 1)
        self.assertAlmostEqual(float(arrays["epoch_freq_hr_stats"][0, 0]), 29 / 30)

    def test_motion_outliers_are_filtered_per_axis(self):
        start = 1_700_000_000.0
        offsets = np.arange(30, dtype=np.float64)
        hr = np.column_stack((start + offsets, np.full(30, 60.0)))
        motion = np.column_stack((start + offsets, np.ones(30), offsets**2, np.zeros(30)))
        motion[15, 1] = 100
        labels = np.asarray([0], dtype=np.uint8)
        arrays = converter.convert_arrays(
            hr, motion, start, labels, labels, minimum_epochs=1, maximum_epochs=1
        )
        self.assertAlmostEqual(
            float(arrays["signal_1hz"][15, 1]), math.sqrt(1 + 225**2), places=4
        )

    def test_missing_boundary_is_masked_not_extrapolated(self):
        with tempfile.TemporaryDirectory() as folder:
            night = Path(folder)
            write_night(night, 1, short_hr=True)
            hr = converter.read_csv(night / "hr.csv", 2, converter.HR_HEADERS)
            motion = converter.read_csv(night / "motion.csv", 4, converter.MOTION_HEADERS)
            start, dreem, expert = converter.load_labels(night / "labels.mat")
            arrays = converter.convert_arrays(
                hr, motion, start, dreem, expert, minimum_epochs=1, maximum_epochs=1
            )
            self.assertTrue(np.isnan(arrays["signal_1hz"][0, 0]))
            self.assertFalse(bool(arrays["stage_mask"][0]))

    def test_csv_canonicalizes_documented_public_anomalies(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "hr.csv"
            path.write_text("timestamp,hr\n3,70\n1,60\n1,80\n2,65\n7\n")
            values, repairs = converter.read_csv_with_repairs(
                path, 2, converter.HR_HEADERS
            )
            np.testing.assert_allclose(values, [[1, 70], [2, 65], [3, 70]])
            self.assertEqual(
                repairs,
                {
                    "discardedIncompleteFinalRows": 1,
                    "reorderedRows": 4,
                    "duplicateTimestampGroups": 1,
                    "duplicateRowsCollapsed": 1,
                },
            )
            path.write_text("timestamp,hr\n1,60\n2\n3,70\n")
            with self.assertRaises(converter.ConverterError):
                converter.read_csv(path, 2, converter.HR_HEADERS)

    def test_label_tails_align_and_long_nights_truncate_like_source(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "labels.mat"
            savemat(
                path,
                {
                    "recStart": np.asarray([[1_700_000_000.0]]),
                    "dreem_label": np.asarray([0, 1, 2, 3]),
                    "expert_label": np.asarray([0, 1, 2]),
                },
            )
            _, dreem, expert, repairs = converter.load_labels_with_repairs(path)
            np.testing.assert_array_equal(dreem, [0, 1, 2])
            self.assertEqual(repairs["dreemTailEpochsTrimmed"], 1)
            offsets = np.arange(90, dtype=np.float64)
            hr = np.column_stack((1_700_000_000 + offsets, np.full(90, 60.0)))
            motion = np.column_stack((1_700_000_000 + offsets, np.ones((90, 3))))
            arrays = converter.convert_arrays(
                hr, motion, 1_700_000_000, dreem, expert, minimum_epochs=1, maximum_epochs=2
            )
            self.assertEqual(len(arrays["stage_original"]), 2)

    def test_rejects_bad_timestamps_labels_and_duration(self):
        start = 1_700_000_000.0
        labels = np.asarray([0], dtype=np.uint8)
        good = np.column_stack((start + np.arange(30), np.full(30, 60.0)))
        motion = np.column_stack((start + np.arange(30), np.ones((30, 3))))
        with self.assertRaises(converter.ConverterError):
            converter.convert_arrays(good[::-1], motion, start, labels, labels, minimum_epochs=1)
        with self.assertRaises(converter.ConverterError):
            converter.convert_arrays(good, motion, start, np.asarray([7]), np.asarray([7]), minimum_epochs=1)
        with self.assertRaises(converter.ConverterError):
            converter.convert_arrays(good, motion, start, labels, labels)

    def test_cli_converts_a_full_generated_minimum_night(self):
        with tempfile.TemporaryDirectory() as folder:
            night = Path(folder) / "night"
            night.mkdir()
            write_night(night, 600)
            output = Path(folder) / "aligned"
            subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "converter.py"),
                    str(night),
                    str(output),
                    "--subject-id",
                    "generated-subject-a",
                    "--night-id",
                    "generated-night-a",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            receipt = json.loads(output.with_suffix(".receipt.json").read_text())
            expected = json.loads((ROOT / "generated-converter-receipt.json").read_text())
            self.assertEqual(receipt, expected)
            self.assertEqual(receipt["counts"]["epochs"], 600)
            self.assertEqual(receipt["counts"]["sourceExpertEpochs"], 600)
            self.assertEqual(receipt["counts"]["truncatedTailEpochs"], 0)
            self.assertFalse(receipt["modelReady"])
            self.assertEqual(receipt["unsupportedAuthorFields"], ["personalized_circadian_clock"])
            self.assertFalse(receipt["brainstemExecutionEnabled"])
            self.assertTrue(output.with_suffix(".npz").is_file())


if __name__ == "__main__":
    unittest.main()
