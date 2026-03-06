"""
Neutral Minds — Automated test suite for the Medical Triage Expert System.

Tests cover:
  - Correct triage classification at each urgency level
  - Priority ordering (critical > urgent > moderate > low)
  - Edge cases: no symptoms, invalid symptoms, complex overlapping symptoms
  - Engine management: add, clear, idempotent add, available symptoms
"""

import sys
import os
import unittest

# Ensure the project root is on the path so we can import from interface/
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "interface"))

try:
    from main import TriageEngine, run_triage_for_symptoms
except ImportError as e:
    print(f"Import error: {e}")
    print("Ensure interface/main.py and knowledge_base/expert_system.pl exist.")
    sys.exit(1)


class TestCriticalRules(unittest.TestCase):
    """Test that critical conditions are classified correctly."""

    def test_chest_pain_and_breathing(self):
        """Chest pain + shortness of breath → CRITICAL"""
        result = run_triage_for_symptoms(["chest_pain", "shortness_of_breath"])
        self.assertEqual(result["level"], "critical")
        self.assertTrue(any("cardiac" in e.lower() or "pulmonary" in e.lower()
                            for e in result["explanations"]))

    def test_chest_pain_and_arm_pain(self):
        """Chest pain + left arm pain → CRITICAL"""
        result = run_triage_for_symptoms(["chest_pain", "left_arm_pain"])
        self.assertEqual(result["level"], "critical")
        self.assertTrue(any("myocardial" in e.lower()
                            for e in result["explanations"]))

    def test_unresponsive(self):
        """Unresponsive → CRITICAL"""
        result = run_triage_for_symptoms(["unresponsive"])
        self.assertEqual(result["level"], "critical")

    def test_severe_bleeding(self):
        """Severe bleeding → CRITICAL"""
        result = run_triage_for_symptoms(["severe_bleeding"])
        self.assertEqual(result["level"], "critical")

    def test_seizure(self):
        """Seizure → CRITICAL"""
        result = run_triage_for_symptoms(["seizure"])
        self.assertEqual(result["level"], "critical")

    def test_breathing_with_cyanosis(self):
        """Shortness of breath + cyanosis → CRITICAL"""
        result = run_triage_for_symptoms(["shortness_of_breath", "cyanosis"])
        self.assertEqual(result["level"], "critical")

    def test_stroke_signs(self):
        """Sudden numbness + confusion + severe headache → CRITICAL (stroke)"""
        result = run_triage_for_symptoms(["sudden_numbness", "confusion", "severe_headache"])
        self.assertEqual(result["level"], "critical")
        self.assertTrue(any("stroke" in e.lower()
                            for e in result["explanations"]))


class TestUrgentRules(unittest.TestCase):
    """Test that urgent conditions are classified correctly."""

    def test_high_fever_vomiting(self):
        """High fever + persistent vomiting → URGENT"""
        result = run_triage_for_symptoms(["high_fever", "persistent_vomiting"])
        self.assertEqual(result["level"], "urgent")

    def test_high_fever_stiff_neck(self):
        """High fever + stiff neck → URGENT (meningitis risk)"""
        result = run_triage_for_symptoms(["high_fever", "stiff_neck"])
        self.assertEqual(result["level"], "urgent")
        self.assertTrue(any("meningitis" in e.lower()
                            for e in result["explanations"]))

    def test_severe_abdominal_pain(self):
        """Severe abdominal pain → URGENT"""
        result = run_triage_for_symptoms(["severe_abdominal_pain"])
        self.assertEqual(result["level"], "urgent")

    def test_chest_pain_alone(self):
        """Chest pain alone → URGENT (not critical without second symptom)"""
        result = run_triage_for_symptoms(["chest_pain"])
        self.assertEqual(result["level"], "urgent")


class TestModerateRules(unittest.TestCase):
    """Test that moderate conditions are classified correctly."""

    def test_fever_cough(self):
        """Fever + cough → MODERATE"""
        result = run_triage_for_symptoms(["fever", "cough"])
        self.assertEqual(result["level"], "moderate")

    def test_headache_dizziness(self):
        """Headache + dizziness → MODERATE"""
        result = run_triage_for_symptoms(["headache", "dizziness"])
        self.assertEqual(result["level"], "moderate")

    def test_fever_bodyache(self):
        """Fever + body ache → MODERATE"""
        result = run_triage_for_symptoms(["fever", "body_ache"])
        self.assertEqual(result["level"], "moderate")

    def test_joint_pain_swelling(self):
        """Joint pain + swelling → MODERATE"""
        result = run_triage_for_symptoms(["joint_pain", "swelling"])
        self.assertEqual(result["level"], "moderate")


class TestLowRules(unittest.TestCase):
    """Test that low-urgency conditions are classified correctly."""

    def test_headache_alone(self):
        """Headache alone → LOW"""
        result = run_triage_for_symptoms(["headache"])
        self.assertEqual(result["level"], "low")

    def test_runny_nose(self):
        """Runny nose → LOW"""
        result = run_triage_for_symptoms(["runny_nose"])
        self.assertEqual(result["level"], "low")

    def test_sore_throat(self):
        """Sore throat → LOW"""
        result = run_triage_for_symptoms(["sore_throat"])
        self.assertEqual(result["level"], "low")

    def test_fatigue(self):
        """Fatigue → LOW"""
        result = run_triage_for_symptoms(["fatigue"])
        self.assertEqual(result["level"], "low")


class TestNoneAndEdgeCases(unittest.TestCase):
    """Test edge cases: no symptoms, invalid symptoms."""

    def test_no_symptoms(self):
        """No symptoms → NONE"""
        result = run_triage_for_symptoms([])
        self.assertEqual(result["level"], "none")

    def test_invalid_symptom_graceful(self):
        """An unrecognized symptom alone should result in 'none' (no rules match)."""
        result = run_triage_for_symptoms(["made_up_symptom_xyz"])
        self.assertEqual(result["level"], "none")


class TestPriorityOrdering(unittest.TestCase):
    """Test that higher-priority levels always win over lower ones."""

    def test_critical_beats_urgent(self):
        """Chest pain + shortness of breath → CRITICAL (not urgent)."""
        result = run_triage_for_symptoms(["chest_pain", "shortness_of_breath"])
        self.assertEqual(result["level"], "critical")

    def test_urgent_beats_moderate(self):
        """High fever + persistent vomiting → URGENT (not moderate)."""
        result = run_triage_for_symptoms(["high_fever", "persistent_vomiting"])
        self.assertEqual(result["level"], "urgent")

    def test_moderate_beats_low(self):
        """Fever + cough → MODERATE (not low)."""
        result = run_triage_for_symptoms(["fever", "cough"])
        self.assertEqual(result["level"], "moderate")


class TestComplexScenarios(unittest.TestCase):
    """Test complex multi-symptom scenarios."""

    def test_complex_multi_symptom(self):
        """Many symptoms: critical rule should still win."""
        result = run_triage_for_symptoms([
            "chest_pain", "shortness_of_breath", "fever", "cough", "headache"
        ])
        self.assertEqual(result["level"], "critical")

    def test_all_levels_populated(self):
        """With a rich symptom set, multiple levels should appear in all_levels."""
        result = run_triage_for_symptoms([
            "chest_pain", "shortness_of_breath",  # critical
            "high_fever", "persistent_vomiting",   # urgent
            "fever", "cough",                       # moderate
            "headache",                             # low
        ])
        self.assertEqual(result["level"], "critical")
        self.assertIn("urgent", result.get("all_levels", {}))


class TestEngineManagement(unittest.TestCase):
    """Test the TriageEngine's symptom management functions."""

    def setUp(self):
        self.engine = TriageEngine()

    def test_add_and_list_symptoms(self):
        """Symptoms can be added and retrieved."""
        self.engine.add_symptom("fever")
        self.engine.add_symptom("cough")
        current = self.engine.get_current_symptoms()
        self.assertIn("fever", current)
        self.assertIn("cough", current)

    def test_clear_symptoms(self):
        """Clearing symptoms removes all."""
        self.engine.add_symptom("fever")
        self.engine.clear_symptoms()
        current = self.engine.get_current_symptoms()
        self.assertEqual(len(current), 0)

    def test_idempotent_add(self):
        """Adding the same symptom twice does not duplicate it."""
        self.engine.add_symptom("fever")
        self.engine.add_symptom("fever")
        current = self.engine.get_current_symptoms()
        self.assertEqual(current.count("fever"), 1)

    def test_available_symptoms_populated(self):
        """The knowledge base provides a non-empty list of available symptoms."""
        available = self.engine.get_available_symptoms()
        self.assertGreater(len(available), 20)


if __name__ == "__main__":
    unittest.main(verbosity=2)
