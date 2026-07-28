import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("reproduce", ROOT / "reproduce.py")
reproduce = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(reproduce)


class ReproduceContractTest(unittest.TestCase):
    def test_metrics_match_known_matrix(self):
        result = reproduce._metrics([[8, 1, 1], [2, 5, 3], [1, 1, 8]])
        self.assertEqual(result["epochs"], 30)
        self.assertEqual(result["accuracy"], 0.7)
        self.assertEqual(result["classMetrics"]["NREM"]["support"], 10)

    def test_split_nights_share_public_subject(self):
        self.assertEqual(reproduce._subject("slp01a"), reproduce._subject("slp01b"))
        self.assertEqual(reproduce._subject("slp02a"), reproduce._subject("slp02b"))
        self.assertNotEqual(reproduce._subject("slp03"), reproduce._subject("slp04"))

    def test_empty_matrix_is_rejected(self):
        with self.assertRaises(reproduce.ReproductionError):
            reproduce._metrics([[0, 0, 0], [0, 0, 0], [0, 0, 0]])


if __name__ == "__main__":
    unittest.main()

