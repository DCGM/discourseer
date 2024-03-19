from __future__ import annotations
import logging
import pydantic
from typing import Optional, Dict

import numpy as np
import pandas as pd
from irrCAC.raw import CAC

from discourseer.rater import Rater
from discourseer.extraction_topics import ExtractionTopics, single_choice_tag

logger = logging.getLogger()


class IRRResults(pydantic.BaseModel):
    overall: IRRResult
    mean_through_topics: Optional[IRRResult] = None
    topics: Optional[Dict[str, IRRResult]] = {}

    def get_mean_through_topics(self) -> IRRResult:
        if not self.topics:
            return IRRResult()
        return IRRResult(
            fleiss_kappa=self.get_mean('fleiss_kappa'),
            krippendorff_alpha=self.get_mean('krippendorff_alpha'),
            gwet_ac1=self.get_mean('gwet_ac1'),
            majority_agreement=self.get_mean_majority_agreement()
        )

    def get_mean(self, metric: str) -> IRRVariants:
        if not self.topics:
            return IRRVariants()
        return IRRVariants(
            best_case=self.get_mean_value(metric, 'best_case'),
            with_model=self.get_mean_value(metric, 'with_model'),
            worst_case=self.get_mean_value(metric, 'worst_case'),
            without_model=self.get_mean_value(metric, 'without_model')
        )

    def get_mean_value(self, metric: str, variant: str) -> float:
        sum_values = sum([result.model_dump()[metric][variant] for result in self.topics.values()
                          if result.model_dump()[metric][variant] is not None])
        return round(sum_values / len(self.topics), 5)

    def get_mean_majority_agreement(self) -> float | None:
        if not self.topics:
            return None
        sum_values = sum([result.majority_agreement for result in self.topics.values()
                          if result.majority_agreement is not None])
        return round(sum_values / len(self.topics), 5)


class IRRResult(pydantic.BaseModel):
    fleiss_kappa: IRRVariants
    krippendorff_alpha: IRRVariants
    gwet_ac1: IRRVariants
    majority_agreement: Optional[float] = None


class IRRVariants(pydantic.BaseModel):
    best_case: Optional[float] = None
    with_model: Optional[float] = None
    worst_case: Optional[float] = None
    without_model: Optional[float] = None


class IRR:
    TOTAL_AGREEMENT = 1.0
    WORST_CASE_VALUE = '--WORST-CASE--'  # A value that should not be present in the ratings
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
    index_cols = ['file', 'topic_key', 'rating']

    def __init__(self, raters: list[Rater], model_rater: Rater = None, extraction_topics: ExtractionTopics = None):
        self.raters = raters
        self.model_rater = model_rater
        if model_rater:
            self.model_rater.name = self.col_model
        self.extraction_topics = extraction_topics if extraction_topics else ExtractionTopics()

        self.input_columns = []
        self.model_columns = []

        self.results: IRRResults = self.get_inter_rater_reliability()

    def __call__(self) -> IRRResults:
        return self.results

    def get_inter_rater_reliability(self) -> IRRResults:
        if self.model_rater is not None:
            df = self.raters_to_dataframe(self.raters + [self.model_rater])
        else:
            df = self.raters_to_dataframe(self.raters)

        df = self.reorganize_raters(df)
        df = self.clean_data(df)

        if df.empty:
            logger.warning("Empty DataFrame after cleaning. Cannot calculate inter-rater reliability.")
            return IRR.EMPTY_IRR_RESULTS

        self.input_columns = df.columns.difference([self.col_model]).to_list()
        self.model_columns = [self.col_model] if self.col_model in df.columns else []
        topics = df.index.get_level_values('topic_key').unique().to_list()

        df = self.prepare_majority_agreement(df)
        df = self.add_worst_case(df)

        logger.debug(f'Calculating inter-rater reliability for:\n{df}')

        overall_results = self.get_irr_result(df)

        topic_irr_results = {}
        for topic in topics:
            df_topic = df.xs(topic, level='topic_key')
            topic_irr_results[topic] = self.get_irr_result(df_topic)

        irr_results = IRRResults(
            overall=overall_results,
            topics=topic_irr_results
        )

        irr_results.mean_through_topics = irr_results.get_mean_through_topics()
        return irr_results

    def get_irr_result(self, df: pd.DataFrame) -> IRRResult:
        if self.model_rater:
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
        if self.col_model in df.columns:
            df = df.dropna(subset=[self.col_model])

        rows_before = df.shape[0]
        df = df[df.notna().all(axis=1)]
        removed_rows = rows_before - df.shape[0]
        logger.debug(f"Removed {removed_rows}/{rows_before} rows with NaN values.")

        return df

    def add_worst_case(self, df: pd.DataFrame) -> pd.DataFrame:
        df[self.col_worst_case] = IRR.WORST_CASE_VALUE

        df.reset_index(inplace=True)
        df.loc[df['rating'] != single_choice_tag, self.col_worst_case] = 'False'
        df.set_index(['file', 'topic_key', 'rating'], inplace=True)

        return df

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

        if IRR.all_rows_equal(cac.ratings):
            return IRR.TOTAL_AGREEMENT
        else:
            with np.errstate(divide='ignore', invalid='ignore'):
                result = getattr(cac, metric)()['est']['coefficient_value']
            return result

    @staticmethod
    def all_rows_equal(df: pd.DataFrame) -> bool:
        """
        Check if all rows in a DataFrame are equal.
        """
        return df.apply(lambda x: x.nunique(), axis=1).eq(1).all()

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
