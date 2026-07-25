from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
