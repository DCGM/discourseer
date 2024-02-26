import pytest
import logging
import json

import pandas as pd
from irrCAC.raw import CAC

from rater import Rater

logger = logging.getLogger(__name__)


def get_inter_rater_reliability(raters: list[Rater], model_rater: Rater = None) -> dict:
    results = {}
    df = raters_to_dataframe(raters + [model_rater]) if model_rater else raters_to_dataframe(raters)
    df = clean_data_for_kappa(df)

    cac_without_model = CAC(df.loc[:, df.columns != 'model'])
    cac_with_model = CAC(df) if model_rater else None
    logging.debug(f'Calculating inter-rater reliability for:\n{df}')

    without_model, with_model = calc_fleiss_kappa(cac_without_model, cac_with_model)
    results['fleiss'] = {'without_model': without_model, 'with_model': with_model}

    without_model, with_model = calc_kripp_alpha(cac_without_model, cac_with_model)
    results['kripp'] = {'without_model': without_model, 'with_model': with_model}

    without_model, with_model = calc_gwet_ac1(cac_without_model, cac_with_model)
    results['gwet'] = {'without_model': without_model, 'with_model': with_model}

    logging.info(f'Inter-rater reliability results:\n{json.dumps(results, indent=2)}')
    return results


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


def str_dataframe_to_int(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a DataFrame with string values to a DataFrame with integer values.
    """
    df_int = df.copy()
    unique_values = df_int.stack().unique()
    # TODO deal with NaN values somehow...?
    # value_map = {np.nan: pd.nan}, then append...
    value_map = {value: float(i) for i, value in enumerate(unique_values, start=1)}

    df_int = df_int.applymap(lambda x: value_map[x])
    return df_int


def clean_data_for_kappa(df: pd.DataFrame) -> pd.DataFrame:
    df_cleaned = df.copy()
    if 'model' in df_cleaned.columns:
        df_cleaned = df_cleaned.dropna(subset=['model'])

    rows_before = df_cleaned.shape[0]
    df_cleaned = df_cleaned[df_cleaned.notna().all(axis=1)]
    removed_rows = rows_before - df_cleaned.shape[0]
    logger.debug(f"Removed {removed_rows}/{rows_before} rows with NaN values.")

    return df_cleaned


def raters_to_dataframe(raters: list[Rater]) -> pd.DataFrame:
    """
    Convert a list of raters to a pandas DataFrame.

    :param raters: List of raters
    :return: DataFrame
    """
    raters_dict = {}
    for rater in raters:
        rater.name = get_unique_rater_name(rater.name, list(raters_dict.keys()))
        raters_dict[rater.name] = rater.to_series()

    df = pd.DataFrame(raters_dict)
    for col in df.columns:
        df[col] = df[col].astype('string')
    return df


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


def test_irr_equal():
    rater_1 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")
    rater_2 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")
    irr_results = get_inter_rater_reliability([rater_1, rater_2])

    assert irr_results['fleiss']['without_model'] == 1.0
    assert irr_results['fleiss']['with_model'] is None
    assert irr_results['kripp']['without_model'] == 1.0
    assert irr_results['kripp']['with_model'] is None
    assert irr_results['gwet']['without_model'] == 1.0
    assert irr_results['gwet']['with_model'] is None


def test_irr_diff():
    rater_1 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")
    rater_2 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_2.csv")
    irr_results = get_inter_rater_reliability([rater_1, rater_2])

    assert irr_results['fleiss']['without_model'] == pytest.approx(0.8, 0.05)
    assert irr_results['fleiss']['with_model'] is None
    assert irr_results['kripp']['without_model'] == pytest.approx(0.8, 0.05)
    assert irr_results['kripp']['with_model'] is None
    assert irr_results['gwet']['without_model'] == pytest.approx(0.8, 0.05)
    assert irr_results['gwet']['with_model'] is None


def test_irr_ignore_nan():
    rater_1 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")
    rater_4 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_4.csv")

    irr_results = get_inter_rater_reliability([rater_1, rater_4])

    assert irr_results['fleiss']['without_model'] == pytest.approx(0.7, 0.05)
    assert irr_results['fleiss']['with_model'] is None
    assert irr_results['kripp']['without_model'] == pytest.approx(0.7, 0.05)
    assert irr_results['kripp']['with_model'] is None
    assert irr_results['gwet']['without_model'] == pytest.approx(0.7, 0.05)
    assert irr_results['gwet']['with_model'] is None
