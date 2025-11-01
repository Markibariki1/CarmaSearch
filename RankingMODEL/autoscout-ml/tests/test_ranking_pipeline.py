import os
import sys
import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.ranking_pipeline import HybridRankingEngine


class HybridRankingEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = HybridRankingEngine()
        self.target = {
            "id": "target",
            "price": 25000,
            "mileage_km": 45000,
            "year": 2021,
            "fuel_type": "Petrol",
            "transmission": "Automatic",
            "body_type": "SUV",
            "power_kw": 120,
            "color": "Black",
            "drive_train": "AWD",
        }

    def test_prefers_cheaper_candidate_with_matching_specs(self) -> None:
        candidates = [
            {
                "id": "cheaper",
                "price": 23500,
                "mileage_km": 43000,
                "year": 2021,
                "make": "Brand",
                "model": "Model X",
                "fuel_type": "Petrol",
                "transmission": "Automatic",
                "body_type": "SUV",
                "power_kw": 118,
                "color": "Black",
                "drive_train": "AWD",
            },
            {
                "id": "expensive",
                "price": 26500,
                "mileage_km": 43000,
                "year": 2021,
                "make": "Brand",
                "model": "Model X",
                "fuel_type": "Petrol",
                "transmission": "Automatic",
                "body_type": "SUV",
                "power_kw": 118,
                "color": "Black",
                "drive_train": "AWD",
            },
        ]

        ranked = self.engine.rank_candidates(self.target, candidates)
        self.assertEqual(ranked[0]["vehicle"]["id"], "cheaper")
        self.assertGreater(ranked[0]["scores"]["final"], ranked[1]["scores"]["final"])

    def test_handles_missing_optional_attributes(self) -> None:
        candidates = [
            {
                "id": "complete",
                "price": 25500,
                "mileage_km": 47000,
                "year": 2020,
                "make": "Brand",
                "model": "Model X",
                "fuel_type": "Petrol",
                "transmission": "Automatic",
                "body_type": "SUV",
                "power_kw": 120,
                "color": "Black",
                "drive_train": "AWD",
            },
            {
                "id": "partial",
                "price": 25500,
                "make": "Brand",
                "model": "Model X",
            },
        ]

        ranked = self.engine.rank_candidates(self.target, candidates)
        self.assertEqual(len(ranked), 2)
        for entry in ranked:
            final_score = entry["scores"]["final"]
            self.assertGreaterEqual(final_score, 0.0)
            self.assertLessEqual(final_score, 1.0)

    def test_preference_boost_for_color_match(self) -> None:
        target = {
            **self.target,
            "preferred_color": "Blue",
        }

        candidates = [
            {
                "id": "preferred",
                "price": 25500,
                "mileage_km": 46000,
                "year": 2021,
                "make": "Brand",
                "model": "Model X",
                "fuel_type": "Petrol",
                "transmission": "Automatic",
                "body_type": "SUV",
                "power_kw": 118,
                "color": "Blue",
                "drive_train": "AWD",
            },
            {
                "id": "non_preferred",
                "price": 25500,
                "mileage_km": 46000,
                "year": 2021,
                "make": "Brand",
                "model": "Model X",
                "fuel_type": "Petrol",
                "transmission": "Automatic",
                "body_type": "SUV",
                "power_kw": 118,
                "color": "Black",
                "drive_train": "AWD",
            },
        ]

        ranked = self.engine.rank_candidates(target, candidates)
        self.assertEqual(ranked[0]["vehicle"]["id"], "preferred")
        self.assertGreater(ranked[0]["scores"]["preference"], ranked[1]["scores"]["preference"])


if __name__ == "__main__":
    unittest.main()
