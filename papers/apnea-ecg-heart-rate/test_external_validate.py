import importlib.util
import unittest
from datetime import datetime
from pathlib import Path

import numpy


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "external_validate", HERE / "external_validate.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ExternalValidationContractTest(unittest.TestCase):
    def test_event_mapping_crosses_midnight_without_changing_duration(self):
        events = MODULE._events(
            "23:58:00 APNEA-O 20\n00:02:00 HYP-C 30\n",
            datetime(2026, 8, 4, 23, 55),
            600,
        )
        self.assertEqual(events, [(180.0, 200.0), (420.0, 450.0)])

    def test_minute_metrics_keep_exact_denominators(self):
        self.assertEqual(
            MODULE._round_metrics(MODULE._matrix_metrics([[8, 2], [3, 7]])),
            {
                "sensitivity": 0.7,
                "specificity": 0.8,
                "balancedAccuracy": 0.75,
                "accuracy": 0.75,
            },
        )

    def test_participant_bootstrap_tolerates_undefined_class_metric(self):
        participants = [
            {
                "sensitivity": None,
                "specificity": 0.8,
                "balancedAccuracy": None,
                "accuracy": 0.8,
            },
            {
                "sensitivity": 0.6,
                "specificity": 0.9,
                "balancedAccuracy": 0.75,
                "accuracy": 0.7,
            },
        ]
        result = MODULE._bootstrap(participants, numpy)
        self.assertEqual(result["sensitivity"], {"low": 0.6, "high": 0.6})
        self.assertEqual(result["specificity"], {"low": 0.8, "high": 0.9})


if __name__ == "__main__":
    unittest.main()
