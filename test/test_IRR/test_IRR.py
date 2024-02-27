import unittest
import pytest

import numpy as np

from discourseer.inter_rater_reliability import IRR
from discourseer.rater import Rater


class TestIRR(unittest.TestCase):
    def test_irr_equal(self):
        rater_1 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")
        rater_2 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")

        # ignore mathematical warnings caused by raters having no variance
        with np.errstate(divide='ignore', invalid='ignore'):
            irr_results = IRR([rater_1, rater_2])()

        self.assertEqual(irr_results['fleiss']['without_model'], 1.0)
        self.assertEqual(irr_results['fleiss']['with_model'], None)
        assert irr_results['kripp']['without_model'] == 1.0
        assert irr_results['kripp']['with_model'] is None
        assert irr_results['gwet']['without_model'] == 1.0
        assert irr_results['gwet']['with_model'] is None

    def test_irr_diff(self):
        rater_1 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")
        rater_2 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_2.csv")
        irr_results = IRR([rater_1, rater_2])()

        assert irr_results['fleiss']['without_model'] == pytest.approx(0.8, 0.05)
        assert irr_results['fleiss']['with_model'] is None
        assert irr_results['kripp']['without_model'] == pytest.approx(0.8, 0.05)
        assert irr_results['kripp']['with_model'] is None
        assert irr_results['gwet']['without_model'] == pytest.approx(0.8, 0.05)
        assert irr_results['gwet']['with_model'] is None

    def test_irr_ignore_nan(self):
        rater_1 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")
        rater_4 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_4.csv")

        irr_results = IRR([rater_1, rater_4])()

        assert irr_results['fleiss']['without_model'] == pytest.approx(0.7, 0.05)
        assert irr_results['fleiss']['with_model'] is None
        assert irr_results['kripp']['without_model'] == pytest.approx(0.7, 0.05)
        assert irr_results['kripp']['with_model'] is None
        assert irr_results['gwet']['without_model'] == pytest.approx(0.7, 0.05)
        assert irr_results['gwet']['with_model'] is None
