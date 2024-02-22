import pytest
import logging

from pyirr import kappam_fleiss
import pandas as pd

from rater import Rater

logger = logging.getLogger(__name__)


def calc_fleiss_kappa(raters: list[Rater]) -> float:
    """
    Calculate Fleiss' Kappa for a list of raters.

    :param raters: List of raters
    :return: Fleiss' Kappa
    """
    df = raters_to_dataframe(raters)
    df = clean_data_for_kappa(df)
    logger.debug(f'DataFrame head:\n{df.head()}')

    result = kappam_fleiss(df)
    return result.value


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


def test_fleiss_kappa_equal():
    rater_1 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")
    rater_2 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")
    kappa = calc_fleiss_kappa([rater_1, rater_2])
    assert kappa == 1.0


def test_fleiss_kappa_2_diff():
    rater_1 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")
    rater_2 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_2.csv")
    kappa = calc_fleiss_kappa([rater_1, rater_2])
    assert kappa == pytest.approx(0.8, 0.05)


def test_fleiss_kappa_ignore_nan():
    rater_1 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_1.csv")
    rater_4 = Rater.from_csv("data/texts-vlach-ratings-1ofN/rater_4.csv")
    kappa = calc_fleiss_kappa([rater_1, rater_4])
    # df = raters_to_dataframe([rater_1, rater_2])

    assert kappa == pytest.approx(0.7, 0.05)


if __name__ == "__main__":
    # test_fleiss_kappa_equal()
    # test_fleiss_kappa_2_diff()
    test_fleiss_kappa_ignore_nan()
