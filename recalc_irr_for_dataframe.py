# input: dataframe, output: recalculated inter-rater reliability

import argparse
import os

import numpy as np
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

    df = df.replace({'nan': np.nan, 0: '0', 1: '1', 2: '2', 3: '3', 4: '4', 5: '5',
                     4.0: '4', 5.0: '5'})
    df = df.astype('string')

    print(f'Recalculating IRR for dataframe:\n{df}')
    cac = CAC(df)
    kripp = IRR.get_cac_metric(cac, 'krippendorff')
    print(f'Krippendorff\'s alpha for this dataframe is: {kripp}')

    # save dataframe to csv without header and index if needed
    # df.to_csv('output.csv', header=False, index=False)


if __name__ == '__main__':
    main()
