from __future__ import annotations
import logging
import os

import pydantic
from typing import Optional, Dict

import numpy as np
import pandas as pd
from irrCAC.raw import CAC

from discourseer.rater import Rater
from discourseer.extraction_prompts import ExtractionPrompts, single_choice_tag
from discourseer import utils

logger = logging.getLogger()


class IRRVariants(pydantic.BaseModel):
    best_case: Optional[float] = None
    with_model: Optional[float] = None
    worst_case: Optional[float] = None
    without_model: Optional[float] = None


# define types for exporting IRR results
IRRResultsFlattened = Dict[str, IRRVariants]
IRRResultsFlattenedOneVariant = Dict[str, float]


class IRRResults(pydantic.BaseModel):
    overall: IRRResult
    mean_through_prompts: Optional[IRRResult] = None
    prompts: Optional[Dict[str, IRRResult]] = {}

    def get_mean_through_prompts(self) -> IRRResult:
        if not self.prompts:
            return IRRResult()
        return IRRResult(
            fleiss_kappa=self.get_mean('fleiss_kappa'),
            krippendorff_alpha=self.get_mean('krippendorff_alpha'),
            gwet_ac1=self.get_mean('gwet_ac1'),
            majority_agreement=self.get_mean_majority_agreement()
        )

    def get_mean(self, metric: str) -> IRRVariants:
        if not self.prompts:
            return IRRVariants()
        return IRRVariants(
            best_case=self.get_mean_value(metric, 'best_case'),
            with_model=self.get_mean_value(metric, 'with_model'),
            worst_case=self.get_mean_value(metric, 'worst_case'),
            without_model=self.get_mean_value(metric, 'without_model')
        )

    def get_mean_value(self, metric: str, variant: str) -> float:
        sum_values = sum([result.model_dump()[metric][variant] for result in self.prompts.values()
                          if result.model_dump()[metric][variant] is not None])
        return round(sum_values / len(self.prompts), 5)

    def get_mean_majority_agreement(self) -> float | None:
        if not self.prompts:
            return None
        sum_values = sum([result.majority_agreement for result in self.prompts.values()
                          if result.majority_agreement is not None])
        return round(sum_values / len(self.prompts), 5)

    def to_dict_of_results(self) -> Dict[str, IRRResult]:
        results: Dict[str, IRRResult] = {'overall': self.overall}
        if self.mean_through_prompts is not None:
            results['mean_through_prompts'] = self.mean_through_prompts

        for key, result in self.prompts.items():
            if result is not None:
                results[key] = result

        return results

    def to_dict_of_results_of_metric(self, metric: str) -> IRRResultsFlattened:
        results = self.to_dict_of_results()
        return {k: getattr(v, metric) for k, v in results.items() if hasattr(v, metric)}
    
    def to_dict_of_results_of_metric_and_variant(self, metric: str, variant: str) -> IRRResultsFlattenedOneVariant:
        results = self.to_dict_of_results_of_metric(metric)
        return {k: getattr(v, variant) for k, v in results.items() if hasattr(v, variant)}

    def get_summary(self) -> Dict:
        results = {'overall': self.overall.model_dump()}
        if self.mean_through_prompts is not None:
            results['mean_through_prompts'] = self.mean_through_prompts.model_dump()
        return results

    def get_one_metric(self, metric: str) -> Dict:
        if not hasattr(self.overall, metric):
            return self.get_summary()

        results = {'overall': self.overall.get_metric(metric)}
        if self.mean_through_prompts is not None:
            results['mean_through_prompts'] = self.mean_through_prompts.get_metric(metric)

        results['prompts'] = {}
        for key, result in self.prompts.items():
            if result is not None:
                results['prompts'][key] = result.get_metric(metric)
        return results
    
    def get_one_metric_and_variant(self, metric: str, variant: str) -> Dict:
        results = self.get_one_metric(metric)

        results['overall'] = results['overall'][variant]
        if self.mean_through_prompts is not None:
            results['mean_through_prompts'] = results['mean_through_prompts'][variant]

        for key, result in results['prompts'].items():
            if result is not None:
                results['prompts'][key] = result[variant]
        
        return results

    def is_empty(self) -> bool:
        return self.overall.fleiss_kappa.without_model is None

    @classmethod
    def from_json_file(cls, file: str) -> IRRResults:
        return utils.json_file_to_pydantic(file, cls)


class IRRResult(pydantic.BaseModel):
    fleiss_kappa: IRRVariants
    krippendorff_alpha: IRRVariants
    gwet_ac1: IRRVariants
    majority_agreement: Optional[float] = None

    def get_metric(self, metric: str):
        return self.model_dump()[metric]


class IRR:
    DATAFRAME_NAME = 'dataframe.csv'
    TOTAL_AGREEMENT = 1.0
    WORST_CASE_VALUE = '--WORST-CASE'  # A value that should not be present in the ratings
    EMPTY_IRR_RESULTS = IRRResults(
        overall=IRRResult(
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
    index_cols = ['file', 'prompt_key', 'rating']
    col_non_rater_columns = [col_model, col_majority, col_maj_agree_with_model, col_worst_case, col_best_case]
    col_non_input_columns = [col_model, col_majority, col_maj_agree_with_model, col_worst_case, col_best_case]

    def __init__(self, raters: list[Rater] = None, model_rater: Rater = None, df: pd.DataFrame = None,
                 extraction_prompts: ExtractionPrompts = None, out_dir: str = 'IRR_output',
                 calculate_irr_for_options: bool = False):
        self.raters = raters
        self.model_rater = model_rater
        if model_rater:
            self.model_rater.name = self.col_model
        self.extraction_prompts = extraction_prompts if extraction_prompts else ExtractionPrompts()
        self.calculate_irr_for_options = calculate_irr_for_options
        self.out_dir = out_dir
        self.out_dataframe = os.path.join(self.out_dir, self.DATAFRAME_NAME)
        os.makedirs(self.out_dir, exist_ok=True)

        if self.calculate_irr_for_options:
            self.out_prompts_and_options_dir = os.path.join(self.out_dir, 'prompt_and_option_results')
            os.makedirs(self.out_prompts_and_options_dir, exist_ok=True)

        self.input_columns = []
        self.model_columns = []
        self.rater_columns = []

        self.option_results = {}

        if df is not None:
            self.df = df
        else:
            self.df = self.prepare_dataframe_from_raters()
        self.results = self.get_inter_rater_reliability(self.df)

    def __call__(self) -> IRRResults:
        return self.results

    def prepare_dataframe_from_raters(self) -> pd.DataFrame:
        if self.model_rater is not None:
            df = self.raters_to_dataframe(self.raters + [self.model_rater])
        else:
            df = self.raters_to_dataframe(self.raters)
        self.rater_columns = df.columns.difference(self.col_non_rater_columns).to_list()

        df_before_cleaning = df.copy()

        df = self.reorganize_raters(df)
        df = self.clean_data(df)

        if df.shape[0] == 0:
            logger.warning("Empty DataFrame after cleaning. Cannot calculate inter-rater reliability.")
            logging.debug(f"Data before cleaning (see whole dataframe in {self.out_dataframe}):\n{df_before_cleaning}")
            df_before_cleaning.to_csv(self.out_dataframe)
            return IRR.EMPTY_IRR_RESULTS

        return df

    def get_inter_rater_reliability(self, df: pd.DataFrame) -> IRRResults:
        self.input_columns = df.columns.difference(self.col_non_input_columns).to_list()
        self.model_columns = [self.col_model] if self.col_model in df.columns else []
        prompt_keys = df.index.get_level_values('prompt_key').unique().to_list()

        df = self.prepare_majority_agreement(df)
        df = self.add_worst_case(df)

        logger.debug(f'Calculating inter-rater reliability for (see whole in {self.out_dataframe}):\n{df}')
        # print(f'Calculating inter-rater reliability for (see whole in {self.out_dataframe}):\n{df}')
        df.to_csv(self.out_dataframe)

        overall_results = self.get_irr_result(df)

        prompt_irr_results = {}
        for prompt_key in prompt_keys:
            logger.info(f"Calculating IRR for prompt {prompt_key}")
            df_prompt = df.xs(prompt_key, level='prompt_key')
            prompt_irr_results[prompt_key] = self.get_irr_result(df_prompt)

            # save df_prompt to csv
            if self.calculate_irr_for_options:
                df_prompt_output_file = os.path.join(self.out_prompts_and_options_dir,
                                                     f"dataframe__{prompt_key.replace(' ', '_')}")
                df_prompt.to_csv(df_prompt_output_file + '.csv')
                self.calculate_irr_for_each_option(df_prompt, prompt_key, df_prompt_output_file)

        if self.calculate_irr_for_options:
            utils.dict_to_json_file(
                self.option_results,
                os.path.join(self.out_prompts_and_options_dir, f"irr_kripp_alpha_for_individual_options.json"))
            utils.individual_option_irr_to_csv(
                self.option_results,
                os.path.join(self.out_prompts_and_options_dir, f"irr_kripp_alpha_for_individual_options.csv"))

        irr_results = IRRResults(
            overall=overall_results,
            prompts=prompt_irr_results
        )

        irr_results.mean_through_prompts = irr_results.get_mean_through_prompts()
        self.df = df

        return irr_results

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
        rows_before = df.shape[0]
        df = df.replace('nan', np.nan)
        # replace 'nan' strings with NaN for calculating IRR
        # ('nan' would be treated as a separate category, np.nan is treated as missing value)

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
        df.loc[df['rating'] != single_choice_tag, self.col_worst_case] = df[self.col_majority].apply(self.get_opposite_rating)
        df.set_index(['file', 'prompt_key', 'rating'], inplace=True)

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

    def calculate_irr_for_each_option(self, df: pd.DataFrame, prompt_key: str, out_file: str):
        df.reset_index(inplace=True)
        unique_options = df['rating'].unique().tolist()

        if len(unique_options) < 2:
            return

        # get index_cols without 'prompt_key'
        index_cols_without_prompt = self.index_cols.copy()
        index_cols_without_prompt.remove('prompt_key')

        df.set_index(index_cols_without_prompt, inplace=True)
        self.option_results[prompt_key] = {}

        # calculate IRR for each option
        for option in unique_options:
            df_option = df.xs(option, level='rating')
            if df_option.shape[0] == 0:
                logger.debug(f"No ratings for option {option} in prompt {prompt_key}. Skipping IRR calculation.")
                continue

            out_file_option = f"{out_file}__{option.replace(' ', '_').replace('/', '_or_')}.csv"
            df_option.to_csv(out_file_option)
            option_irr_kripp = self.get_irr_result(df_option).krippendorff_alpha.without_model
            self.option_results[prompt_key][option] = option_irr_kripp

        return

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
