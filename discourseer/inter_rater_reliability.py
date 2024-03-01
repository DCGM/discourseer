import logging

import pandas as pd
from irrCAC.raw import CAC

from discourseer.rater import Rater

logger = logging.getLogger(__name__)


class IRR:
    TOTAL_AGREEMENT = 1.0

    def __init__(self, raters: list[Rater], model_rater: Rater = None):
        self.raters = raters
        self.model_rater = model_rater
        if model_rater:
            self.model_rater.name = "model"

        self.results = self.get_inter_rater_reliability()

    def __call__(self) -> dict:
        return self.results

    def get_inter_rater_reliability(self) -> dict:
        results = {}

        if self.model_rater is not None:
            df = self.raters_to_dataframe(self.raters + [self.model_rater])
        else:
            df = self.raters_to_dataframe(self.raters)

        df = IRR.clean_data(df)

        if df.empty:
            logging.warning("Empty DataFrame after cleaning. Cannot calculate inter-rater reliability.")
            return results

        results['majority agreement'] = IRR.calc_majority_agreement(df)

        logging.debug(f'Calculating inter-rater reliability for:\n{df}')
        cac_without_model = CAC(df.loc[:, df.columns != 'model'])
        cac_with_model = CAC(df) if self.model_rater else None

        without_model, with_model = IRR.calc_fleiss_kappa(cac_without_model, cac_with_model)
        results["fleiss' kappa"] = {'without_model': without_model, 'with_model': with_model}

        without_model, with_model = IRR.calc_kripp_alpha(cac_without_model, cac_with_model)
        results["Krippendorf's alpha"] = {'without_model': without_model, 'with_model': with_model}

        without_model, with_model = IRR.calc_gwet_ac1(cac_without_model, cac_with_model)
        results["Gwet's AC1"] = {'without_model': without_model, 'with_model': with_model}

        return results

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

        return majority_agreement

    @staticmethod
    def calc_fleiss_kappa(cac_without_model: CAC, cac_with_model: CAC = None) -> tuple[float, float | None]:
        """
        Calculate Fleiss' Kappa for a list of raters.
        """
        if IRR.all_rows_equal(cac_without_model.ratings):
            result_without_model = IRR.TOTAL_AGREEMENT
        else:
            result_without_model = cac_without_model.fleiss()['est']['coefficient_value']

        if cac_with_model is None:
            result_with_model = None
            logging.debug(f"Fleiss' Kappa for human raters: {result_without_model:.3f}, "
                          f"with model: {None}")
        else:
            if IRR.all_rows_equal(cac_with_model.ratings):
                result_with_model = IRR.TOTAL_AGREEMENT
            else:
                result_with_model = cac_with_model.fleiss()['est']['coefficient_value']
            logging.debug(f"Fleiss' Kappa for human raters: {result_without_model:.3f}, "
                          f"with model: {result_with_model:.3f}")

        return result_without_model, result_with_model

    @staticmethod
    def calc_kripp_alpha(cac_without_model: CAC, cac_with_model: CAC) -> tuple[float, float | None]:
        """
        Calculate Krippendorff's Alpha for a list of raters.
        """
        if IRR.all_rows_equal(cac_without_model.ratings):
            result_without_model = IRR.TOTAL_AGREEMENT
        else:
            result_without_model = cac_without_model.krippendorff()['est']['coefficient_value']

        if cac_with_model is None:
            result_with_model = None
            logging.debug(f"Krippendorff's Alpha for human raters: {result_without_model:.3f}, "
                          f"with model: {None}")
        else:
            if IRR.all_rows_equal(cac_with_model.ratings):
                result_with_model = IRR.TOTAL_AGREEMENT
            else:
                result_with_model = cac_with_model.krippendorff()['est']['coefficient_value']
            logging.debug(f"Krippendorff's Alpha for human raters: {result_without_model:.3f}, "
                          f"with model: {result_with_model:.3f}")

        return result_without_model, result_with_model

    @staticmethod
    def calc_gwet_ac1(cac_without_model: CAC, cac_with_model: CAC) -> tuple[float, float | None]:
        """
        Calculate Gwet's AC1 for a list of raters.
        """
        if IRR.all_rows_equal(cac_without_model.ratings):
            result_without_model = IRR.TOTAL_AGREEMENT
        else:
            result_without_model = cac_without_model.gwet()['est']['coefficient_value']

        if cac_with_model is None:
            result_with_model = None
            logging.debug(f"Gwet's AC1 for human raters: {result_without_model:.3f}, "
                          f"with model: {None}")
        else:
            if IRR.all_rows_equal(cac_with_model.ratings):
                result_with_model = IRR.TOTAL_AGREEMENT
            else:
                result_with_model = cac_with_model.gwet()['est']['coefficient_value']
            logging.debug(f"Gwet's AC1 for human raters: {result_without_model:.3f}, "
                          f"with model: {result_with_model:.3f}")

        return result_without_model, result_with_model

    @staticmethod
    def all_rows_equal(df: pd.DataFrame) -> bool:
        """
        Check if all rows in a DataFrame are equal.
        """
        return df.apply(lambda x: x.nunique(), axis=1).eq(1).all()

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
