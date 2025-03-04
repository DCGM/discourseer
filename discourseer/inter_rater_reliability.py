from __future__ import annotations
import logging
import os
from enum import Enum

import pydantic
from typing import Optional, Dict, List

import numpy as np
import pandas as pd
from irrCAC.raw import CAC

from discourseer.rater import Rater
from discourseer.codebook import single_choice_tag
from discourseer import utils
from discourseer.utils import name_to_path

logger = logging.getLogger()


class IRRResults(pydantic.BaseModel):
    irr_result: IRRResult = None  # mean of all question IRR results
    questions: Optional[Dict[str, IRRQuestionResult]] = {}

    def calc_mean_through_questions(self) -> IRRResult:
        if not self.questions:
            return IRRResult()

        self.irr_result = IRRResult.calc_mean_of_IRRResults([result.irr_result for result in self.questions.values()])
        self.irr_result.description = IRRResultDescription.mean_irr_through_questions
        return self.irr_result

    def to_dict_of_results(self) -> Dict[str, IRRResult]:
        results: Dict[str, IRRResult] = {}
        if self.irr_result is not None:
            results['irr_result'] = self.irr_result

        for question_id, irr_question_result in self.questions.items():
            if irr_question_result is not None:
                results[question_id] = irr_question_result.irr_result

        return results

    def to_dict_of_results_of_metric(self, metric: str) -> Dict[str, IRRVariants]:
        results = self.to_dict_of_results()
        return {k: getattr(v, metric) for k, v in results.items() if hasattr(v, metric)}
    
    def to_dict_of_results_of_metric_and_variant(self, metric: str, variant: str) -> Dict[str, float]:
        results = self.to_dict_of_results_of_metric(metric)
        return {k: getattr(v, variant) for k, v in results.items() if hasattr(v, variant)}

    def get_summary(self) -> Dict:
        results: Dict[str, dict] = {}
        if self.irr_result is not None:
            results['irr_result'] = self.irr_result.model_dump()
        return results

    def get_metric(self, metric: str) -> Dict[str, dict]:
        results = {}
        if self.irr_result is not None:
            results['irr_result'] = self.irr_result.get_metric(metric)

        results['questions'] = {}
        for key, irr_question_result in self.questions.items():
            if irr_question_result is not None:
                results['questions'][key] = irr_question_result.get_metric(metric)
        return results

    def get_metric_and_variant(self, metric: str, variant: str) -> Dict:
        results = self.get_metric(metric)

        if 'irr_result' in results:
            results['irr_result'] = results['irr_result'][variant]

        for key, result in results['questions'].items():
            if result is not None:
                results['questions'][key] = result[variant]
        
        return results

    def select(self, questions: List[str] = None, options: List[str] = None,
               metrics: List[str] = None, variants: List[str] = None,
               include_multiple_choice: bool = True, include_single_choice: bool = True) -> Dict:
        results = {'irr_result': self.irr_result.select(questions, options, metrics, variants, include_multiple_choice, include_single_choice)}

        selected_questions: Dict[str, IRRQuestionResult] = {}

        for question_id, irr_question_result in self.questions.items():
            if not questions or question_id in questions:
                if irr_question_result.multiple_choice and include_multiple_choice:
                    selected_questions[question_id] = irr_question_result.select(questions, options, metrics, variants, include_multiple_choice, include_single_choice)
                elif not irr_question_result.multiple_choice and include_single_choice:
                    selected_questions[question_id] = irr_question_result.select(questions, options, metrics, variants, include_multiple_choice, include_single_choice)

        if not selected_questions:
            return results

        results['questions'] = selected_questions
        return results

    def is_empty(self) -> bool:
        return (self.irr_result is None or
                self.irr_result.fleiss_kappa.without_model is None or
                not self.questions)

    @classmethod
    def from_json_file(cls, file: str) -> IRRResults:
        return utils.json_file_to_pydantic(file, cls)


class IRRQuestionResult(pydantic.BaseModel):
    multiple_choice: bool
    irr_result: IRRResult = None
    options: Optional[Dict[str, IRRResult]] = {}

    def calc_mean_through_options(self) -> IRRResult:
        if not self.options:
            return IRRResult()

        self.irr_result = IRRResult.calc_mean_of_IRRResults([result for result in self.options.values()])
        self.irr_result.description = IRRResultDescription.mean_irr_through_options
        return self.irr_result

    def get_metric(self, metric: str):
        results = {}
        if self.irr_result is not None:
            results['irr_result'] = self.irr_result.get_metric(metric)

        results['options'] = {}
        for key, irr_option_result in self.options.items():
            if irr_option_result is not None:
                results['options'][key] = irr_option_result.get_metric(metric)
        return results

    def select(self, questions: List[str] = None, options: List[str] = None,
               metrics: List[str] = None, variants: List[str] = None,
               include_multiple_choice: bool = True, include_single_choice: bool = True) -> Dict:
        results = {'irr_result': self.irr_result.select(questions, options, metrics, variants, include_multiple_choice, include_single_choice)}
        if not options:
            results['options'] = {k: v.select(questions, options, metrics, variants, include_multiple_choice, include_single_choice) for k, v in self.options.items()}
            return results

        selected_options: Dict[str, IRRResult] = {}

        for option_id, irr_result in self.options.items():
            if option_id in options:
                selected_options[option_id] = irr_result.select(questions, options, metrics, variants, include_multiple_choice, include_single_choice)

        if not selected_options:
            return results

        results['options'] = selected_options
        return results


class IRRResult(pydantic.BaseModel):
    description: Optional[str] = None
    fleiss_kappa: IRRVariants
    krippendorff_alpha: IRRVariants
    gwet_ac1: IRRVariants
    majority_agreement: Optional[float] = None

    def get_metric(self, metric: str):
        if hasattr(self, metric):
            return getattr(self, metric)
        return None

    def select(self, questions: List[str] = None, options: List[str] = None,
               metrics: List[str] = None, variants: List[str] = None,
               include_multiple_choice: bool = True, include_single_choice: bool = True) -> Dict:
        if not metrics:
            return self.model_dump()

        results = {'description': self.description}
        for metric in metrics:
            if hasattr(self, metric) and (metric not in ['description']):
                if isinstance(getattr(self, metric), IRRVariants):
                    results[metric] = getattr(self, metric).select(questions, options, metrics, variants, include_multiple_choice, include_single_choice)
                else:
                    results[metric] = getattr(self, metric)

        return results

    @staticmethod
    def calc_mean_of_IRRResults(results: list[IRRResult]) -> IRRResult:
        if not results:
            return IRRResult()
        return IRRResult(
            fleiss_kappa=IRRResult.calc_mean_of_IRRVariants([result.fleiss_kappa for result in results]),
            krippendorff_alpha=IRRResult.calc_mean_of_IRRVariants([result.krippendorff_alpha for result in results]),
            gwet_ac1=IRRResult.calc_mean_of_IRRVariants([result.gwet_ac1 for result in results]),
            majority_agreement=IRRResult.calc_mean_of_values([result.majority_agreement for result in results])
        )

    @staticmethod
    def calc_mean_of_IRRVariants(results: list[IRRVariants]) -> IRRVariants:
        if not results:
            return IRRVariants()
        return IRRVariants(
            best_case=IRRResult.calc_mean_of_values([result.best_case for result in results]),
            with_model=IRRResult.calc_mean_of_values([result.with_model for result in results]),
            worst_case=IRRResult.calc_mean_of_values([result.worst_case for result in results]),
            without_model=IRRResult.calc_mean_of_values([result.without_model for result in results])
        )

    @staticmethod
    def calc_mean_of_values(values: list[float]) -> float:
        if not values:
            return None
        values = [value for value in values if value is not None]
        if not values:
            return None
        return round(sum(values) / len(values), 5)


class IRRVariants(pydantic.BaseModel):
    best_case: Optional[float] = None
    with_model: Optional[float] = None
    worst_case: Optional[float] = None
    without_model: Optional[float] = None

    def select(self, questions: List[str] = None, options: List[str] = None,
            metrics: List[str] = None, variants: List[str] = None,
            include_multiple_choice: bool = True, include_single_choice: bool = True) -> Dict:
        if not variants:
            return self.model_dump()

        results = {}
        for variant in variants:
            if hasattr(self, variant):
                results[variant] = getattr(self, variant)

        return results

class IRRResultDescription(str, Enum):
    # string enums to make it serializable to JSON
    mean_irr_through_questions = "mean IRR through questions"
    mean_irr_through_options = "mean IRR through options"
    irr_for_single_choice_question = "IRR for single choice question"
    irr_for_this_option = "IRR for this option"


class IRR:
    DATAFRAME_NAME = 'dataframe.csv'
    TOTAL_AGREEMENT = 1.0
    WORST_CASE_VALUE = '--WORST-CASE'  # A value that should not be present in the ratings
    EMPTY_IRR_RESULTS = IRRResults(
        irr_result=IRRResult(
            fleiss_kappa=IRRVariants(),
            krippendorff_alpha=IRRVariants(),
            gwet_ac1=IRRVariants()
        ),
    )

    col_majority = 'majority'
    col_maj_agree_with_model = 'maj_agreement_with_model'
    col_model = 'model'
    col_worst_case = 'worst_case'
    col_best_case = col_majority
    index_cols = utils.result_dataframe_index_columns()
    col_non_rater_columns = [col_model, col_majority, col_maj_agree_with_model, col_worst_case, col_best_case]
    col_non_input_columns = [col_model, col_majority, col_maj_agree_with_model, col_worst_case, col_best_case]

    def __init__(self, raters: list[Rater] = None, model_rater: Rater = None, df: pd.DataFrame = None,
                 out_dir: str = 'IRR_output',
                 export_dataframes_for_options: bool = False):
        self.raters = raters
        self.model_rater = model_rater
        if model_rater:
            self.model_rater.name = self.col_model

        # self.calculate_irr_for_options = True
        self.export_dataframes_for_options = export_dataframes_for_options
        self.out_dir = out_dir
        self.out_dataframe = os.path.join(self.out_dir, self.DATAFRAME_NAME)
        os.makedirs(self.out_dir, exist_ok=True)

        if self.export_dataframes_for_options:
            self.out_questions_and_options_dir = os.path.join(self.out_dir, 'question_and_option_results')
            os.makedirs(self.out_questions_and_options_dir, exist_ok=True)

        self.input_columns = []
        self.model_columns = []
        self.rater_columns = []

        self.option_results = {}

        if df is None:  # df not provided as an argument, prepare it from raters
            self.df = self.prepare_dataframe_from_raters()
            self.df = self.preprocess_dataframe(self.df)
        else:
            self.df = self.preprocess_dataframe(df)
            self.df[self.col_maj_agree_with_model] = self.df[self.col_maj_agree_with_model].astype('object').replace({'False': False, 'True': True}).astype('bool')

        if self.df is None:  # empty DataFrame after cleaning
            self.results = IRR.EMPTY_IRR_RESULTS
        else:
            self.results = self.get_inter_rater_reliability(self.df)

    def __call__(self) -> IRRResults:
        return self.results

    def prepare_dataframe_from_raters(self) -> pd.DataFrame:
        if self.model_rater is not None:
            df = self.raters_to_dataframe(self.raters + [self.model_rater])
        else:
            df = self.raters_to_dataframe(self.raters)

        df = self.reorganize_raters(df)
        return df

    def preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df_before_cleaning = df.copy()
        df = self.clean_data(df)

        if df.shape[0] == 0:
            logger.warning("Empty DataFrame after cleaning. Cannot calculate inter-rater reliability.")
            logger.debug(f"Data before cleaning (see whole dataframe in {self.out_dataframe}):\n{df_before_cleaning}")
            df_before_cleaning.to_csv(self.out_dataframe.replace('.csv', '_before_cleaning.csv'))
            return None

        return df

    def get_inter_rater_reliability(self, df: pd.DataFrame) -> IRRResults:
        self.input_columns = df.columns.difference(self.col_non_input_columns).to_list()
        self.model_columns = [self.col_model] if self.col_model in df.columns else []
        question_ids = df.index.get_level_values(self.index_cols[1]).unique().to_list()

        df = self.prepare_majority_agreement(df)
        df = self.add_worst_case(df)

        logger.debug(f'Calculating inter-rater reliability for (see whole in {self.out_dataframe}):\n{df}')
        df.to_csv(self.out_dataframe)

        irr_question_results = {}
        for question_id in question_ids:
            logger.info(f"Calculating IRR for question {question_id}")

            df_question = df.xs(question_id, level=self.index_cols[1])
            unique_options = list(df_question.index.get_level_values('option_id').unique())

            if len(unique_options) == 0:
                logger.warning(f"No ratings for question_id {question_id}. Skipping IRR calculation.")
                continue
            elif len(unique_options) == 1 and unique_options[0] == single_choice_tag:
                logger.debug(f'calculating IRR for single choice question {question_id}')
                # question is single choice, calculate IRR for the question as a whole
                irr_result=self.get_irr_result(df_question)
                irr_result.description = IRRResultDescription.irr_for_single_choice_question
                irr_question_results[question_id] = IRRQuestionResult(irr_result=irr_result, multiple_choice=False)
            else:  # multiple choice question
                irr_question_results[question_id] = self.calculate_irr_for_each_option(
                    df_question, unique_options, question_id)

        irr_results = IRRResults(
            questions=irr_question_results
        )
        irr_results.calc_mean_through_questions()
        self.df = df

        # kripp_alphas_with_model = irr_results.to_dict_of_results_of_metric_and_variant('krippendorff_alpha', 'with_model')
        kripp_alphas_with_model = irr_results.select(metrics=['krippendorff_alpha'], variants=['with_model'])
        utils.dict_to_json_file(
            kripp_alphas_with_model,
            os.path.join(self.out_dir, f"irr_kripp_alpha_with_model.json"))

        return irr_results

    def calculate_irr_for_each_option(self, df_question: pd.DataFrame, unique_options: list[str], question_id: str) -> IRRQuestionResult:
        option_results: Dict[str, IRRResult] = {}

        for option in unique_options:
            df_option = df_question.xs(option, level='option_id')
            if df_option.shape[0] == 0:
                logger.debug(f"No ratings for option {option} in question_id {question_id}. Skipping IRR calculation.")
                continue

            logger.debug(f'calculating IRR for option "{option}" in multi choice question {question_id}')

            option_irr_result = self.get_irr_result(df_option)
            option_irr_result.description = IRRResultDescription.irr_for_this_option
            option_results[option] = option_irr_result

            # export dataframes for options
            if self.export_dataframes_for_options:
                df_option_output_file = os.path.join(self.out_questions_and_options_dir,
                                                     f"dataframe__{name_to_path(question_id)}__{name_to_path(option)}.csv")
                df_option.to_csv(df_option_output_file)

        irr_question_result = IRRQuestionResult(
            options=option_results,
            multiple_choice=True
        )
        irr_question_result.calc_mean_through_options()

        return irr_question_result

    def get_irr_result(self, df: pd.DataFrame) -> IRRResult:
        if self.model_rater or self.col_model in df.columns:
            cac_with_model = CAC(df.loc[:, self.input_columns + self.model_columns])
        else:
            cac_with_model = None

        maj_agreement = self.calc_majority_agreement(df)
        cac_without_model = CAC(df.loc[:, self.input_columns])
        cac_worst_case = CAC(df.loc[:, self.input_columns + [self.col_worst_case]])
        cac_best_case = CAC(df.loc[:, self.input_columns + [self.col_best_case]])

        fleiss_kappa = IRR.calc_fleiss_kappa(cac_without_model, cac_with_model, cac_worst_case, cac_best_case)
        kripp_alpha = IRR.calc_kripp_alpha(cac_without_model, cac_with_model, cac_worst_case, cac_best_case)
        gwet_ac1 = IRR.calc_gwet_ac1(cac_without_model, cac_with_model, cac_worst_case, cac_best_case)

        return IRRResult(
            fleiss_kappa=fleiss_kappa,
            krippendorff_alpha=kripp_alpha,
            gwet_ac1=gwet_ac1,
            majority_agreement=maj_agreement
        )

    def prepare_majority_agreement(self, df: pd.DataFrame):
        if self.col_majority in df.columns and self.col_maj_agree_with_model in df.columns:
            return df

        if self.col_majority not in df.columns:
            df[self.col_majority] = df.loc[:, self.input_columns].mode(axis=1).iloc[:, 0]

        if len(self.model_columns) == 1:
            df[self.col_maj_agree_with_model] = df[self.col_majority] == df[self.model_columns[0]]
        elif len(self.model_columns) > 1:
            df[self.col_maj_agree_with_model] = None
            logger.warning(f"Cannot calculate majority agreement. "
                           f"More than one model columns found: {self.model_columns}")
        return df

    def calc_majority_agreement(self, df: pd.DataFrame) -> float | None:
        """
        Calculate majority agreement of a model to raters.
        """
        if self.col_majority not in df.columns or self.col_maj_agree_with_model not in df.columns:
            df = self.prepare_majority_agreement(df)

        if self.col_maj_agree_with_model not in df.columns:
            logger.info(f"Cannot calculate majority agreement. "
                        f"Column '{self.col_maj_agree_with_model}' not found in DataFrame.")
            return None

        majority_agreement = df[self.col_maj_agree_with_model].sum() / df.shape[0]
        return round(majority_agreement, 3)

    def reorganize_raters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get dataFrame with sparse values (possibly lots of NaNs), shift all human rater nonNaN values to the left
        in their rows.
        """
        # df = df.copy()
        df.reset_index(inplace=True)
        df_indexes = df[self.index_cols]

        # separate model and human ratings
        df_model = df[self.col_model] if self.col_model in df.columns else None
        df_raters = df[df.columns.difference([self.col_model] + self.index_cols)].copy()

        # Add padding row to avoid columns being dropped
        df_raters.loc[len(df_raters.index)] = ['<padding>'] * len(df_raters.columns)

        # reorganize human ratings and delete NaN columns
        df_raters_new = pd.DataFrame(
            df_raters.iloc[:, ::].apply(
                lambda x: x.dropna().tolist(), axis=1).tolist(),
            columns=df_raters.columns[::]
        ).iloc[:, ::]

        # drop unused padding row and columns
        df_raters_new.drop(df_raters_new.tail(1).index, inplace=True)  # drop padding row
        df_raters_new.dropna(axis=1, how='all', inplace=True)  # drop NaN columns

        for column in df_raters_new.columns:
            df_raters_new[column] = df_raters_new[column].astype('string')

        # join model and human ratings
        df_all = pd.concat([df_indexes, df_raters_new, df_model], axis=1)

        df_all.set_index(self.index_cols, inplace=True)
        return df_all

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        self.rater_columns = df.columns.difference(self.col_non_rater_columns).to_list()
        rows_before = df.shape[0]
        df = df.replace('nan', np.nan)
        # replace 'nan' strings with NaN for calculating IRR
        # ('nan' would be treated as a separate category, np.nan should be treated as missing value)

        # if model column is present, remove rows with NaN in model column
        if self.col_model in df.columns:
            df = df[df[self.col_model].notna()]

        # remove rows where all self.rater_columns are NaN
        df = df.dropna(subset=self.rater_columns, how='all')

        removed_rows = rows_before - df.shape[0]
        logger.debug(f"Removed {removed_rows}/{rows_before} rows with NaN values.")

        return df

    def add_worst_case(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.col_worst_case in df.columns:
            return df

        df[self.col_worst_case] = IRR.WORST_CASE_VALUE

        df.reset_index(inplace=True)
        # set worst case as opposite of majority agreement
        df.loc[df['option_id'] != single_choice_tag, self.col_worst_case] = df[self.col_majority].apply(self.get_opposite_rating)
        df.set_index(self.index_cols, inplace=True)

        df[self.col_worst_case] = df[self.col_worst_case].astype('string')
        return df
    
    @staticmethod
    def get_opposite_rating(rating: str) -> str:
        # check for NA first
        if pd.isna(rating):
            return rating
        elif rating == 'True':
            return 'False'
        elif rating == 'False':
            return 'True'
        return rating

    def get_reorganized_raters(self) -> pd.DataFrame:
        return self.df.loc[:, self.input_columns]

    @staticmethod
    def calc_fleiss_kappa(cac_without_model: CAC, cac_with_model: CAC = None, cac_worst_case: CAC = None,
                          cac_best_case: CAC = None) -> IRRVariants:
        """
        Calculate Fleiss' Kappa for a list of raters.
        """
        result = IRRVariants(
            without_model=IRR.get_cac_metric(cac_without_model, 'fleiss'),
            with_model=IRR.get_cac_metric(cac_with_model, 'fleiss'),
            worst_case=IRR.get_cac_metric(cac_worst_case, 'fleiss'),
            best_case=IRR.get_cac_metric(cac_best_case, 'fleiss')
        )
        return result

    @staticmethod
    def calc_kripp_alpha(cac_without_model: CAC, cac_with_model: CAC = None, cac_worst_cast: CAC = None,
                         cac_best_case: CAC = None) -> IRRVariants:
        """
        Calculate Krippendorff's Alpha for a list of raters.
        """
        result = IRRVariants(
            without_model=IRR.get_cac_metric(cac_without_model, 'krippendorff'),
            with_model=IRR.get_cac_metric(cac_with_model, 'krippendorff'),
            worst_case=IRR.get_cac_metric(cac_worst_cast, 'krippendorff'),
            best_case=IRR.get_cac_metric(cac_best_case, 'krippendorff')
        )
        return result

    @staticmethod
    def calc_gwet_ac1(cac_without_model: CAC, cac_with_model: CAC = None, cac_worst_cast: CAC = None,
                      cac_best_case: CAC = None) -> IRRVariants:
        """
        Calculate Gwet's AC1 for a list of raters.
        """
        result = IRRVariants(
            without_model=IRR.get_cac_metric(cac_without_model, 'gwet'),
            with_model=IRR.get_cac_metric(cac_with_model, 'gwet'),
            worst_case=IRR.get_cac_metric(cac_worst_cast, 'gwet'),
            best_case=IRR.get_cac_metric(cac_best_case, 'gwet')
        )
        return result

    @staticmethod
    def get_cac_metric(cac: CAC = None, metric: str = None) -> float | None:
        if cac is None:
            logger.debug("No CAC object provided. Empty data.")
            return None

        if metric is None:
            logger.debug("No metric provided.")
            return None

        if IRR.single_row(cac.ratings) or IRR.all_rows_equal(cac.ratings):
            return IRR.TOTAL_AGREEMENT
        elif IRR.is_total_disagreement(cac):
            return IRR.get_total_disagreement_value(metric)
        else:
            with np.errstate(divide='ignore', invalid='ignore'):
                result = getattr(cac, metric)()['est']['coefficient_value']
            return result

    @staticmethod
    def single_row(df: pd.DataFrame) -> bool:
        """
        Check if there is only one row and all values are the same.
        """
        return df.shape[0] < 2

    @staticmethod
    def all_rows_equal(df: pd.DataFrame) -> bool:
        """
        Check if all rows in a DataFrame are equal.
        """
        return df.apply(lambda x: x.nunique(), axis=1).eq(1).all()

    @staticmethod
    def is_total_disagreement(cac: CAC) -> bool:
        """
        Check if there is less or equal unique values than categories in the DataFrame.
        """
        return cac.ratings.nunique().sum() <= len(cac.categories)

    @staticmethod
    def get_total_disagreement_value(metric: str) -> float:
        """
        Get the value for total disagreement.
        """
        if metric in ['fleiss', 'krippendorff']:
            return -1.0
        elif metric == 'gwet':
            return 0.0
        return -42.0

    @staticmethod
    def raters_to_dataframe(raters: list[Rater]) -> pd.DataFrame:
        """
        Convert a list of raters to a pandas DataFrame.

        :param raters: List of raters
        :return: DataFrame
        """
        raters_dict = {}
        for rater in raters:
            rater.name = IRR.get_unique_rater_name(rater.name, list(raters_dict.keys()))
            raters_dict[rater.name] = rater.to_series()

        # check if all raters have the same length
        lens = [len(rater) for rater in raters_dict.values()]
        if len(set(lens)) != 1:
            logger.warning(f"Raters have different lengths of ratings: {lens}. Is it possible the ratings come from different sets of texts?")

        df = pd.DataFrame(raters_dict)
        for col in df.columns:
            df[col] = df[col].astype('string')
        return df

    @staticmethod
    def get_unique_rater_name(name: str, names: list[str]) -> str:
        """
        Return a unique name based on the input name and a list of existing names.
        """
        if name not in names:
            return name

        offset = 1
        while name in names:
            name = f"{name}_{offset}"
            offset += 1
        return name
