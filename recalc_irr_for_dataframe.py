# input: dataframe, output: recalculated inter-rater reliability

import argparse
import os

import pandas as pd
from typing import List
from irrCAC.raw import CAC
from discourseer.inter_rater_reliability import IRR


def parse_args():
    parser = argparse.ArgumentParser(description='Recalculate IRR for a dataframe')
    parser.add_argument('input', type=str, help='input dataframe')
    return parser.parse_args()


def main():
    args = parse_args()
    if not os.path.isfile(args.input):
        raise ValueError(f'Input file {args.input} does not exist')

    print(f'Loading dataframe from {args.input}')
    df = pd.read_csv(args.input).set_index('file')

    print(f'Recalculating IRR for dataframe:\n{df}')
    print(f'df.dtypes: {df.dtypes}')
    cac = CAC(df)
    kripp = IRR.get_cac_metric(cac, 'krippendorff')
    print(f'Krippendorff\'s alpha for this dataframe is: {kripp}')

    gwet = IRR.get_cac_metric(cac, 'gwet')
    print(f'Gwet\'s AC1 for this dataframe is: {gwet}')

    # replace all True values to 1 and False values to 0
    df = df.replace({True: 1, False: 0})
    print(f'Recalculating IRR for dataframe after replacing True to 1 and False to 0:\n{df}')
    print(f'df.dtypes: {df.dtypes}')
    cac = CAC(df)
    kripp = IRR.get_cac_metric(cac, 'krippendorff')
    print(f'Krippendorff\'s alpha for this dataframe is: {kripp}')

    # save dataframe to csv without header and index if needed
    # df.to_csv('output.csv', header=False, index=False)


if __name__ == '__main__':
    main()
