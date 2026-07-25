from __future__ import annotations

import unittest

from gateway.nutri_ai_lite import calculate_health_metrics
from services.nutri_ai_service.core.profile.normalization import (
    normalize_activity,
    normalize_diet,
    normalize_goal,
)


class GradioProfileNormalizationTests(unittest.TestCase):
    def test_normalizes_saved_frontend_profile_values(self):
        self.assertEqual(normalize_activity("extreme"), "very_active")
        self.assertEqual(normalize_goal("lose_weight"), "lose weight")
        self.assertEqual(normalize_diet("keto"), "low carb")

    def test_normalizes_all_noncanonical_frontend_goals(self):
        self.assertEqual(normalize_goal("gain_muscle"), "gain weight")
        self.assertEqual(normalize_goal("improve_health"), "maintain weight")
        self.assertEqual(normalize_diet("paleo"), "balanced")

    def test_is_tolerant_of_hyphens_case_and_spacing(self):
        self.assertEqual(normalize_goal("  LOSE-WEIGHT  "), "lose weight")
        self.assertEqual(normalize_activity("Very-Active"), "very_active")
        self.assertEqual(normalize_diet("HIGH_PROTEIN"), "high protein")
        self.assertEqual(normalize_diet("omnivore"), "balanced")

    def test_health_metrics_accept_legacy_frontend_values(self):
        metrics = calculate_health_metrics(
            {
                "age": 30,
                "gender": "male",
                "height_cm": 175,
                "weight_kg": 80,
                "activity_level": "extreme",
                "goal": "lose_weight",
                "diet_type": "keto",
            }
        )
        self.assertIn("calorie_target", metrics)
        self.assertLess(metrics["calorie_target"], metrics["tdee"])


if __name__ == "__main__":
    unittest.main()
