import logging

import pandas as pd
from irrCAC.raw import CAC

from discourseer.rater import Rater

logger = logging.getLogger(__name__)


class IRR:
    def __init__(self, raters: list[Rater], model_rater: Rater = None):
        self.raters = raters
        self.model_rater = model_rater
        self.results = self.get_inter_rater_reliability()

    def get_inter_rater_reliability(self) -> dict:
        results = {}

        # df = pd.DataFrame()
        if self.model_rater is not None:
            df = self.raters_to_dataframe(self.raters + [self.model_rater])
        else:
            df = self.raters_to_dataframe(self.raters)

        df = IRR.clean_data(df)

        cac_without_model = CAC(df.loc[:, df.columns != 'model'])
        cac_with_model = CAC(df) if self.model_rater else None
        logging.debug(f'Calculating inter-rater reliability for:\n{df}')

        without_model, with_model = IRR.calc_fleiss_kappa(cac_without_model, cac_with_model)
        results['fleiss'] = {'without_model': without_model, 'with_model': with_model}

        without_model, with_model = IRR.calc_kripp_alpha(cac_without_model, cac_with_model)
        results['kripp'] = {'without_model': without_model, 'with_model': with_model}

        without_model, with_model = IRR.calc_gwet_ac1(cac_without_model, cac_with_model)
        results['gwet'] = {'without_model': without_model, 'with_model': with_model}

        return results

    def __call__(self) -> dict:
        return self.results

    @staticmethod
    def calc_fleiss_kappa(cac_without_model: CAC, cac_with_model: CAC = None) -> tuple[float, float]:
        """
        Calculate Fleiss' Kappa for a list of raters.
        """
        result_without_model = cac_without_model.fleiss()['est']['coefficient_value']

        if cac_with_model is None:
            result_with_model = None
            logging.debug(f"Fleiss' Kappa for human raters: {result_without_model:.3f}, "
                          f"with model: {None}")
        else:
            result_with_model = cac_with_model.fleiss()['est']['coefficient_value']
            logging.debug(f"Fleiss' Kappa for human raters: {result_without_model:.3f}, "
                          f"with model: {result_with_model:.3f}")

        return result_without_model, result_with_model

    @staticmethod
    def calc_kripp_alpha(cac_without_model: CAC, cac_with_model: CAC) -> tuple[float, float]:
        """
        Calculate Krippendorff's Alpha for a list of raters.
        """
        result_without_model = cac_without_model.krippendorff()['est']['coefficient_value']

        if cac_with_model is None:
            result_with_model = None
            logging.debug(f"Krippendorff's Alpha for human raters: {result_without_model:.3f}, "
                          f"with model: {None}")
        else:
            result_with_model = cac_with_model.krippendorff()['est']['coefficient_value']
            logging.debug(f"Krippendorff's Alpha for human raters: {result_without_model:.3f}, "
                          f"with model: {result_with_model:.3f}")

        return result_without_model, result_with_model

    @staticmethod
    def calc_gwet_ac1(cac_without_model: CAC, cac_with_model: CAC) -> tuple[float, float]:
        """
        Calculate Gwet's AC1 for a list of raters.
        """
        result_without_model = cac_without_model.gwet()['est']['coefficient_value']

        if cac_with_model is None:
            result_with_model = None
            logging.debug(f"Gwet's AC1 for human raters: {result_without_model:.3f}, "
                          f"with model: {None}")
        else:
            result_with_model = cac_with_model.gwet()['est']['coefficient_value']
            logging.debug(f"Gwet's AC1 for human raters: {result_without_model:.3f}, "
                          f"with model: {result_with_model:.3f}")

        return result_without_model, result_with_model

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
