from __future__ import annotations
import logging
import pydantic
from typing import Optional

import pandas as pd
from irrCAC.raw import CAC

from discourseer.rater import Rater
from discourseer.extraction_topics import ExtractionTopics

logger = logging.getLogger()


class IRRResults(pydantic.BaseModel):
    fleiss_kappa: IRRResult
    krippendorff_alpha: IRRResult
    gwet_ac1: IRRResult
    majority_agreement: Optional[float] = None


class IRRResult(pydantic.BaseModel):
    without_model: Optional[float] = None
    with_model: Optional[float] = None
    worst_case: Optional[float] = None


class IRR:
    TOTAL_AGREEMENT = 1.0
    WORST_CASE_VALUE = '--WORST-CASE--'  # A value that should not be present in the ratings
    EMPTY_IRR_RESULTS = IRRResults(
        fleiss_kappa=IRRResult(),
        krippendorff_alpha=IRRResult(),
        gwet_ac1=IRRResult(),
        majority_agreement=None
    )

    def __init__(self, raters: list[Rater], model_rater: Rater = None, extraction_topics: ExtractionTopics = None):
        self.raters = raters
        self.model_rater = model_rater
        if model_rater:
            self.model_rater.name = "model"
        self.extraction_topics = extraction_topics if extraction_topics else ExtractionTopics()

        self.results: IRRResults = self.get_inter_rater_reliability()

    def __call__(self) -> IRRResults:
        return self.results

    def get_inter_rater_reliability(self) -> IRRResults:
        if self.model_rater is not None:
            df = self.raters_to_dataframe(self.raters + [self.model_rater])
        else:
            df = self.raters_to_dataframe(self.raters)

        # logging.debug(f'Data before reorganizing:\n{df}')
        df = IRR.reorganize_raters(df)
        # logging.debug(f'Data before cleaning:\n{df}')
        df = IRR.clean_data(df)

        if df.empty:
            logging.warning("Empty DataFrame after cleaning. Cannot calculate inter-rater reliability.")
            return IRR.EMPTY_IRR_RESULTS

        maj_agreement = IRR.calc_majority_agreement(df)

        logging.debug(f'Calculating inter-rater reliability for:\n{df}')

        cac_without_model = CAC(df.loc[:, df.columns != 'model'])
        cac_with_model = CAC(df) if self.model_rater else None
        df_worst_case = self.create_worst_case_df(df)
        cac_worst_case = CAC(df_worst_case)

        fleiss_kappa = IRR.calc_fleiss_kappa(cac_without_model, cac_with_model, cac_worst_case)
        kripp_alpha = IRR.calc_kripp_alpha(cac_without_model, cac_with_model, cac_worst_case)
        gwet_ac1 = IRR.calc_gwet_ac1(cac_without_model, cac_with_model, cac_worst_case)

        return IRRResults(
            fleiss_kappa=fleiss_kappa,
            krippendorff_alpha=kripp_alpha,
            gwet_ac1=gwet_ac1,
            majority_agreement=maj_agreement
        )

    @staticmethod
    def calc_majority_agreement(df: pd.DataFrame) -> float | None:
        """
        Calculate majority agreement of a model to raters.
        """
        if 'model' not in df.columns:
            return None

        df['majority'] = df.loc[:, df.columns != 'model'].mode(axis=1).iloc[:, 0]
        df['agreement'] = df['majority'] == df['model']
        majority_agreement = df['agreement'].sum() / df.shape[0]
        logger.debug(f"Majority agreement of human raters with model: {majority_agreement:.3f}")
        del df['majority'], df['agreement']

        return round(majority_agreement, 5)

    @staticmethod
    def calc_fleiss_kappa(cac_without_model: CAC, cac_with_model: CAC = None, cac_worst_cast: CAC = None) -> IRRResult:
        """
        Calculate Fleiss' Kappa for a list of raters.
        """
        result = IRRResult(
            without_model=IRR.get_cac_metric(cac_without_model, 'fleiss'),
            with_model=IRR.get_cac_metric(cac_with_model, 'fleiss'),
            worst_case=IRR.get_cac_metric(cac_worst_cast, 'fleiss')
        )

        logging.debug(f"Fleiss' Kappa results: {result}")
        return result

    @staticmethod
    def calc_kripp_alpha(cac_without_model: CAC, cac_with_model: CAC = None, cac_worst_cast: CAC = None) -> IRRResult:
        """
        Calculate Krippendorff's Alpha for a list of raters.
        """
        result = IRRResult(
            without_model=IRR.get_cac_metric(cac_without_model, 'krippendorff'),
            with_model=IRR.get_cac_metric(cac_with_model, 'krippendorff'),
            worst_case=IRR.get_cac_metric(cac_worst_cast, 'krippendorff')
        )

        logging.debug(f"Krippendorff's Alpha results: {result}")

        return result

    @staticmethod
    def calc_gwet_ac1(cac_without_model: CAC, cac_with_model: CAC = None, cac_worst_cast: CAC = None) -> IRRResult:
        """
        Calculate Gwet's AC1 for a list of raters.
        """
        result = IRRResult(
            without_model=IRR.get_cac_metric(cac_without_model, 'gwet'),
            with_model=IRR.get_cac_metric(cac_with_model, 'gwet'),
            worst_case=IRR.get_cac_metric(cac_worst_cast, 'gwet')
        )

        logging.debug(f"Gwet's AC1 results: {result}")

        return result

    @staticmethod
    def get_cac_metric(cac: CAC = None, metric: str = None) -> float | None:
        if cac is None:
            logging.debug("No CAC object provided. Empty data.")
            return None

        if metric is None:
            logging.debug("No metric provided.")
            return None

        if IRR.all_rows_equal(cac.ratings):
            return IRR.TOTAL_AGREEMENT
        else:
            return getattr(cac, metric)()['est']['coefficient_value']

    @staticmethod
    def all_rows_equal(df: pd.DataFrame) -> bool:
        """
        Check if all rows in a DataFrame are equal.
        """
        return df.apply(lambda x: x.nunique(), axis=1).eq(1).all()

    @staticmethod
    def reorganize_raters(df: pd.DataFrame) -> pd.DataFrame:
        """Get dataFrame with sparse values (possibly lots of NaNs), shift all human rater nonNaN values to the left
        in their rows.
        """
        df = df.copy()
        # reset index
        df.reset_index(inplace=True)
        index_columns = ['file', 'topic_key', 'rating']
        df_indexes = df[index_columns]

        # separate model and human ratings
        df_model = None
        if 'model' in df.columns:
            df_model = df['model']
        df_raters = df[df.columns.difference(['model'] + index_columns)].copy()

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

        # reset index to multiindex
        df_all.set_index(index_columns, inplace=True)

        return df_all

    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        df_cleaned = df.copy()
        if 'model' in df_cleaned.columns:
            df_cleaned = df_cleaned.dropna(subset=['model'])

        rows_before = df_cleaned.shape[0]
        df_cleaned = df_cleaned[df_cleaned.notna().all(axis=1)]
        removed_rows = rows_before - df_cleaned.shape[0]
        logger.debug(f"Removed {removed_rows}/{rows_before} rows with NaN values.")

        return df_cleaned

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

    @staticmethod
    def create_worst_case_df(df: pd.DataFrame) -> pd.DataFrame:
        df_worst_case = df.copy()
        df_worst_case['model'] = IRR.WORST_CASE_VALUE

        df_worst_case.reset_index(inplace=True)
        df_worst_case.loc[df_worst_case['rating'] != 'single_choice', 'model'] = 'False'
        df_worst_case.set_index(['file', 'topic_key', 'rating'], inplace=True)

        return df_worst_case
