import os
import unittest

from discourseer.inter_rater_reliability import IRR
from discourseer.rater import Rater
from run_discourseer import Discourseer


class TestIRRWithoutModel(unittest.TestCase):
    dir = os.path.join(os.path.dirname(__file__), 'IRR_texts')
    codebook = Discourseer.load_codebook('', os.path.join(os.path.dirname(__file__),
                                                        'codebook.json'))

    def test_irr_equal(self):
        rater_1 = Rater.from_csv(os.path.join(self.dir, 'texts-vlach-ratings-1ofN', 'rater_1.csv'),
                                 codebook=self.codebook)
        rater_2 = Rater.from_csv(os.path.join(self.dir, 'texts-vlach-ratings-1ofN', 'rater_1.csv'),
                                 codebook=self.codebook)
        irr_results = IRR([rater_1, rater_2], out_dir='test/test_output_IRR')()

        self.assertEqual(irr_results.overall.fleiss_kappa.without_model, 1.0)
        self.assertEqual(irr_results.overall.fleiss_kappa.with_model, None)
        self.assertEqual(irr_results.overall.krippendorff_alpha.without_model, 1.0)
        self.assertEqual(irr_results.overall.krippendorff_alpha.with_model, None)
        self.assertEqual(irr_results.overall.gwet_ac1.without_model, 1.0)
        self.assertEqual(irr_results.overall.gwet_ac1.with_model, None)

    def test_irr_diff(self):
        rater_1 = Rater.from_csv(os.path.join(self.dir, 'texts-vlach-ratings-1ofN', 'rater_1.csv'), self.codebook)
        rater_2 = Rater.from_csv(os.path.join(self.dir, 'texts-vlach-ratings-1ofN', 'rater_2.csv'), self.codebook)
        irr_results = IRR([rater_1, rater_2], out_dir='test/test_output_IRR')()

        self.assertAlmostEqual(irr_results.overall.fleiss_kappa.without_model, 0.89, 1)
        self.assertEqual(irr_results.overall.fleiss_kappa.with_model, None)
        self.assertAlmostEqual(irr_results.overall.krippendorff_alpha.without_model, 0.89, 1)
        self.assertEqual(irr_results.overall.krippendorff_alpha.with_model, None)
        self.assertAlmostEqual(irr_results.overall.gwet_ac1.without_model, 0.93, 1)
        self.assertEqual(irr_results.overall.gwet_ac1.with_model, None)

    def test_irr_ignore_nan(self):
        rater_1 = Rater.from_csv(os.path.join(self.dir, 'texts-vlach-ratings-1ofN', 'rater_1.csv'), self.codebook)
        rater_4 = Rater.from_csv(os.path.join(self.dir, 'texts-vlach-ratings-1ofN', 'rater_4.csv'), self.codebook)

        irr_results = IRR([rater_1, rater_4], out_dir='test/test_output_IRR')()

        self.assertAlmostEqual(irr_results.overall.fleiss_kappa.without_model, 0.78, 1)
        self.assertEqual(irr_results.overall.fleiss_kappa.with_model, None)
        self.assertAlmostEqual(irr_results.overall.krippendorff_alpha.without_model, 0.79, 1)
        self.assertEqual(irr_results.overall.krippendorff_alpha.with_model, None)
        self.assertAlmostEqual(irr_results.overall.gwet_ac1.without_model, 0.86, 1)
        self.assertEqual(irr_results.overall.gwet_ac1.with_model, None)


class TestMajAgreement(unittest.TestCase):
    dir = os.path.join(os.path.dirname(__file__), 'maj_agreement')
    codebook = Discourseer.load_codebook('', os.path.join(os.path.dirname(__file__),
                                                        'codebook.json'))

    def test_equal(self):
        rater_1 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'), self.codebook)
        rater_2 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'), self.codebook)
        model_rater = Rater.from_csv(os.path.join(self.dir, 'model_rater_equal.csv'))

        irr_results = IRR([rater_1, rater_2], model_rater, out_dir='test/test_output_IRR')()

        self.assertEqual(irr_results.overall.majority_agreement, 1.0)

    def test_diff(self):
        rater_1 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'), self.codebook)
        rater_2 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'), self.codebook)
        model_rater = Rater.from_csv(os.path.join(self.dir, 'model_rater_75_diff.csv'))

        irr_results = IRR([rater_1, rater_2], model_rater, out_dir='test/test_output_IRR')()

        self.assertEqual(irr_results.overall.majority_agreement, 0.222)


# class TestReorganizingRaters(unittest.TestCase):
#     dir = os.path.join(os.path.dirname(__file__), 'reorganizing_raters')
#
#     def test_no_effect(self):
#         rater_1 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'))
#         rater_2 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'))
#         model_rater = Rater.from_csv(os.path.join(self.dir, 'model_rater.csv'))
#         model_rater.name = "model"
#
#         df = IRR.raters_to_dataframe([rater_1, rater_2, model_rater])
#         new_df = IRR.reorganize_raters(df)
#
#         # print('--------------------')
#         # print(f'original df:\n{df}')
#         # print(f'new_df:\n{new_df}')
#
#         # print('--------------------')
#         # print('new_df.dtypes')
#         # print(new_df.dtypes)
#         # print('df.dtypes')
#         # print(df.dtypes)
#
#         assert_frame_equal(df, new_df)
#
#     def test_remove_rater(self):
#         rater_1 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'))
#         rater_1_1 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'))
#         rater_2 = Rater.from_csv(os.path.join(self.dir, 'rater_2_unique_topic.csv'))
#         model_rater = Rater.from_csv(os.path.join(self.dir, 'model_rater.csv'))
#         model_rater.name = "model"
#
#         df = IRR.raters_to_dataframe([rater_1, rater_1_1, rater_2, model_rater])
#         reorganized_df = IRR.reorganize_raters(df)
#
#         ref_rater_1 = Rater.from_csv(os.path.join(self.dir, 'rater_1_ref.csv'))
#         ref_rater_1.name = "rater_1.csv"
#         ref_df = IRR.raters_to_dataframe([ref_rater_1, rater_1_1, model_rater])
#
#         # print('--------------------------')
#         # print(f'reorganized_df:\n{reorganized_df}')
#         # print(f'ref_df:\n{ref_df}')
#         #
#         # print('Compare result:')
#         # print(reorganized_df.compare(ref_df))
#         #
#         # print('equals results:')
#         # print(reorganized_df.equals(ref_df))
#         #
#         # print('reorganized_df.dtypes')
#         # print(reorganized_df.dtypes)
#         #
#         # print('ref_df.dtypes')
#         # print(ref_df.dtypes)
#
#         assert_frame_equal(reorganized_df, ref_df)  #, check_dtype=False)  # , check_index_type=False)
#
#     def test_no_model(self):
#         rater_1 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'))
#         rater_1_1 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'))
#         rater_2 = Rater.from_csv(os.path.join(self.dir, 'rater_2_unique_topic.csv'))
#
#         df = IRR.raters_to_dataframe([rater_1, rater_1_1, rater_2])
#         reorganized_df = IRR.reorganize_raters(df)
#
#         ref_rater_1 = Rater.from_csv(os.path.join(self.dir, 'rater_1_ref.csv'))
#         ref_rater_1.name = "rater_1.csv"
#         ref_df = IRR.raters_to_dataframe([ref_rater_1, rater_1_1])
#
#         # reorganized_df = reorganized_df.replace(np.nan, pd.NA)
#
#         assert_frame_equal(reorganized_df, ref_df)

