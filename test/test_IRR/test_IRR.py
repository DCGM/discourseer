import os
import unittest
import sys

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

        func_name = sys._getframe().f_code.co_name
        output_dir = os.path.join(self.dir, f'{func_name}_output')    
        irr_results = IRR([rater_1, rater_2], out_dir=output_dir)()

        self.assertEqual(irr_results.overall.fleiss_kappa.without_model, 1.0)
        self.assertEqual(irr_results.overall.fleiss_kappa.with_model, None)
        self.assertEqual(irr_results.overall.krippendorff_alpha.without_model, 1.0)
        self.assertEqual(irr_results.overall.krippendorff_alpha.with_model, None)
        self.assertEqual(irr_results.overall.gwet_ac1.without_model, 1.0)
        self.assertEqual(irr_results.overall.gwet_ac1.with_model, None)

    def test_irr_diff(self):
        rater_1 = Rater.from_csv(os.path.join(self.dir, 'texts-vlach-ratings-1ofN', 'rater_1.csv'), self.codebook)
        rater_2 = Rater.from_csv(os.path.join(self.dir, 'texts-vlach-ratings-1ofN', 'rater_2.csv'), self.codebook)

        func_name = sys._getframe().f_code.co_name
        output_dir = os.path.join(self.dir, f'{func_name}_output')
        irr_results = IRR([rater_1, rater_2], out_dir=output_dir)()

        self.assertAlmostEqual(irr_results.overall.fleiss_kappa.without_model, 0.68295, 1)
        self.assertEqual(irr_results.overall.fleiss_kappa.with_model, None)
        self.assertAlmostEqual(irr_results.overall.krippendorff_alpha.without_model, 0.68775, 1)
        self.assertEqual(irr_results.overall.krippendorff_alpha.with_model, None)
        self.assertAlmostEqual(irr_results.overall.gwet_ac1.without_model, 0.804, 1)
        self.assertEqual(irr_results.overall.gwet_ac1.with_model, None)

    def test_irr_ignore_nan(self):
        rater_1 = Rater.from_csv(os.path.join(self.dir, 'texts-vlach-ratings-1ofN', 'rater_1.csv'), self.codebook)
        rater_4 = Rater.from_csv(os.path.join(self.dir, 'texts-vlach-ratings-1ofN', 'rater_4.csv'), self.codebook)

        func_name = sys._getframe().f_code.co_name
        output_dir = os.path.join(self.dir, f'{func_name}_output')
        irr_results = IRR([rater_1, rater_4], out_dir=output_dir)()

        self.assertAlmostEqual(irr_results.overall.fleiss_kappa.without_model, 0.78, 1)
        self.assertEqual(irr_results.overall.fleiss_kappa.with_model, None)
        self.assertAlmostEqual(irr_results.overall.krippendorff_alpha.without_model, 0.79, 1)
        self.assertEqual(irr_results.overall.krippendorff_alpha.with_model, None)
        self.assertAlmostEqual(irr_results.overall.gwet_ac1.without_model, 0.86, 1)
        self.assertEqual(irr_results.overall.gwet_ac1.with_model, None)

    def test_irr_for_options(self):
        rater_1 = Rater.from_csv(os.path.join(self.dir, 'texts-vlach-ratings-1ofN', 'rater_1.csv'), self.codebook)
        rater_2 = Rater.from_csv(os.path.join(self.dir, 'texts-vlach-ratings-1ofN', 'rater_2.csv'), self.codebook)

        func_name = sys._getframe().f_code.co_name
        output_dir = os.path.join(self.dir, f'{func_name}_output')
        irr_calculator = IRR([rater_1, rater_2], out_dir=output_dir,
                             calculate_irr_for_options=True)

        option_results = irr_calculator.option_results
        place_options = option_results['place']

        self.assertAlmostEqual(place_options['czech-republic'], 0.444, 2)
        self.assertAlmostEqual(place_options['russia'], -0.25, 2)
        self.assertAlmostEqual(place_options['ukraine'], 0.0, 2)
        self.assertAlmostEqual(place_options['other'], 1.0, 2)
        self.assertAlmostEqual(place_options['unknown'], 1.0, 2)
        self.assertAlmostEqual(place_options['slovakia'], 1.0, 2)
        self.assertAlmostEqual(place_options['poland'], 1.0, 2)
        self.assertAlmostEqual(place_options['germany'], 1.0, 2)

class TestMajAgreement(unittest.TestCase):
    dir = os.path.join(os.path.dirname(__file__), 'maj_agreement')
    codebook = Discourseer.load_codebook('', os.path.join(os.path.dirname(__file__),
                                                        'codebook.json'))

    def test_equal(self):
        rater_1 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'), self.codebook)
        rater_2 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'), self.codebook)
        model_rater = Rater.from_csv(os.path.join(self.dir, 'model_rater_equal.csv'), self.codebook)

        func_name = sys._getframe().f_code.co_name
        output_dir = os.path.join(self.dir, f'{func_name}_output')
        irr_results = IRR([rater_1, rater_2], model_rater, out_dir=output_dir)()

        self.assertEqual(irr_results.overall.majority_agreement, 1.0)

    def test_question_level(self):
        rater_1 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'), self.codebook)
        rater_2 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'), self.codebook)
        model_rater = Rater.from_csv(os.path.join(self.dir, 'model_rater_diff.csv'), self.codebook)

        func_name = sys._getframe().f_code.co_name
        output_dir = os.path.join(self.dir, f'{func_name}_output')
        irr_results = IRR([rater_1, rater_2], model_rater, out_dir=output_dir)()

        self.assertAlmostEqual(irr_results.overall.majority_agreement, 0.697, 2)
        self.assertAlmostEqual(irr_results.questions['range'].majority_agreement, 0.0, 2)
        self.assertAlmostEqual(irr_results.questions['genre'].majority_agreement, 0.333, 2)
        self.assertAlmostEqual(irr_results.questions['message-trigger'].majority_agreement, 0.333, 2)
        self.assertAlmostEqual(irr_results.questions['place'].majority_agreement, 0.875, 2)

    def test_option_level(self):
        rater_1 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'), self.codebook)
        rater_2 = Rater.from_csv(os.path.join(self.dir, 'rater_1.csv'), self.codebook)
        model_rater = Rater.from_csv(os.path.join(self.dir, 'model_rater_diff.csv'), self.codebook)

        func_name = sys._getframe().f_code.co_name
        output_dir = os.path.join(self.dir, f'{func_name}_output')
        irr_calculator = IRR([rater_1, rater_2], model_rater, out_dir=output_dir)

        irr_results = irr_calculator()
        self.assertAlmostEqual(irr_results.questions['place'].majority_agreement, 0.875, 2)

        # calculate majority agreement for each option
        df = irr_calculator.df.copy()
        df_question = df.xs('place', level=irr_calculator.index_cols[1])
        unique_options = list(df_question.index.get_level_values('option_id').unique())
        # print(unique_options)
        option_maj_agreements = {}
        for option in unique_options:
            option_df = df_question.xs(option, level='option_id')
            option_maj_agg = irr_calculator.calc_majority_agreement(option_df)
            option_maj_agreements[option] = option_maj_agg
            # print(f'option_maj_agg for {option}: {option_maj_agg}')

        self.assertAlmostEqual(option_maj_agreements['czech-republic'], 0.667, 2)
        self.assertAlmostEqual(option_maj_agreements['russia'], 0.333, 2)
        self.assertAlmostEqual(option_maj_agreements['slovakia'], 1.0, 2)
        self.assertAlmostEqual(option_maj_agreements['poland'], 1.0, 2)
        self.assertAlmostEqual(option_maj_agreements['germany'], 1.0, 2)
        self.assertAlmostEqual(option_maj_agreements['ukraine'], 1.0, 2)
        self.assertAlmostEqual(option_maj_agreements['other'], 1.0, 2)
        self.assertAlmostEqual(option_maj_agreements['unknown'], 1.0, 2)

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

