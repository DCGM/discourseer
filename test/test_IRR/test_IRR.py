import os
import unittest
import pytest

from discourseer.inter_rater_reliability import IRR
from discourseer.rater import Rater


class TestIRRWithoutModel(unittest.TestCase):
    def test_irr_equal(self):
        rater_1 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")
        rater_2 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")
        irr_results = IRR([rater_1, rater_2])().model_dump()

        self.assertEqual(irr_results["fleiss_kappa"]['without_model'], 1.0)
        self.assertEqual(irr_results["fleiss_kappa"]['with_model'], None)
        self.assertEqual(irr_results["krippendorff_alpha"]['without_model'], 1.0)
        self.assertEqual(irr_results["krippendorff_alpha"]['with_model'], None)
        self.assertEqual(irr_results["gwet_ac1"]['without_model'], 1.0)
        self.assertEqual(irr_results["gwet_ac1"]['with_model'], None)

    def test_irr_diff(self):
        rater_1 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")
        rater_2 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_2.csv")
        irr_results = IRR([rater_1, rater_2])().model_dump()

        assert irr_results["fleiss_kappa"]['without_model'] == pytest.approx(0.8, 0.05)
        assert irr_results["fleiss_kappa"]['with_model'] is None
        assert irr_results["krippendorff_alpha"]['without_model'] == pytest.approx(0.8, 0.05)
        assert irr_results["krippendorff_alpha"]['with_model'] is None
        assert irr_results["gwet_ac1"]['without_model'] == pytest.approx(0.8, 0.05)
        assert irr_results["gwet_ac1"]['with_model'] is None

    def test_irr_ignore_nan(self):
        rater_1 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")
        rater_4 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_4.csv")

        irr_results = IRR([rater_1, rater_4])().model_dump()

        assert irr_results["fleiss_kappa"]['without_model'] == pytest.approx(0.7, 0.05)
        assert irr_results["fleiss_kappa"]['with_model'] is None
        assert irr_results["krippendorff_alpha"]['without_model'] == pytest.approx(0.7, 0.05)
        assert irr_results["krippendorff_alpha"]['with_model'] is None
        assert irr_results["gwet_ac1"]['without_model'] == pytest.approx(0.7, 0.05)
        assert irr_results["gwet_ac1"]['with_model'] is None


class TestMajAgreement(unittest.TestCase):
    dir = os.path.join(os.path.dirname(__file__), 'maj_agreement')

    def test_equal(self):
        rater_1 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'))
        rater_2 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'))
        model_rater = Rater.from_csv(os.path.join(self.dir, 'model_rater_equal.csv'))

        irr_results = IRR([rater_1, rater_2], model_rater)().model_dump()

        assert irr_results["majority_agreement"] == 1.0

    def test_diff(self):
        rater_1 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'))
        rater_2 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'))
        model_rater = Rater.from_csv(os.path.join(self.dir, 'model_rater_75_diff.csv'))

        irr_results = IRR([rater_1, rater_2], model_rater)().model_dump()

        assert irr_results["majority_agreement"] == 0.25
