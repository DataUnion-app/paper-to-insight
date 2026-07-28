import importlib.util
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("sample_entropy", ROOT / "algorithm.py")
algorithm = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(algorithm)


def series(count: int = 300) -> list[float]:
    return [
        900 + 35 * math.sin(index / 11) + (index % 7 - 3) * 3
        for index in range(count)
    ]


class SampleEntropyTest(unittest.TestCase):
    def test_is_deterministic_and_finite(self):
        first = algorithm.resting_rr_sample_entropy(series())
        second = algorithm.resting_rr_sample_entropy(series())
        self.assertEqual(first, second)
        self.assertTrue(math.isfinite(first["sampleEntropy"]))
        self.assertGreater(first["templateMatches"], first["extendedMatches"])

    def test_scale_and_offset_do_not_change_normalized_result(self):
        values = series()
        transformed = [value * 1.4 + 100 for value in values]
        self.assertAlmostEqual(
            algorithm.resting_rr_sample_entropy(values)["sampleEntropy"],
            algorithm.resting_rr_sample_entropy(transformed)["sampleEntropy"],
            places=12,
        )

    def test_invalid_or_constant_recording_abstains(self):
        invalid = series()
        invalid[10] = 2500
        self.assertIsNone(algorithm.resting_rr_sample_entropy(invalid))
        self.assertIsNone(algorithm.resting_rr_sample_entropy([900.0] * 300))
        self.assertIsNone(algorithm.resting_rr_sample_entropy(series(239)))

    def test_parameters_are_frozen(self):
        self.assertIsNone(algorithm.sample_entropy(series(), dimension=3))
        self.assertIsNone(algorithm.sample_entropy(series(), tolerance=0.15))


if __name__ == "__main__":
    unittest.main()
