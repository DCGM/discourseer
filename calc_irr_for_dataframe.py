# input: dataframe, output: recalculated inter-rater reliability

import argparse
import os
from typing import List
import shutil
import json

import numpy as np
import pandas as pd
from irrCAC.raw import CAC

from discourseer.inter_rater_reliability import IRR
from run_discourseer import Discourseer
from discourseer import utils


def parse_args():
    parser = argparse.ArgumentParser(description='Recalculate IRR for a dataframe')
    parser.add_argument('--input-dir', type=str,
                        help='input folder containing the csv file with the ratings (output of previous experiment)')
    parser.add_argument('--output-dir', type=str, 
                        help='output folder to save the recalculated IRR results')
    parser.add_argument('--codebook', type=str,
                        help='JSON file containing the codebook (codebok name+version, questions, options...).')
    return parser.parse_args()


def main():
    args = parse_args()

    Calculator(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        codebook=args.codebook
    )()


class Calculator:
    def __init__(self, input_dir: str, output_dir: str, codebook: str = None):
        self.input_dir = input_dir
        if not os.path.isdir(self.input_dir):
            raise ValueError(f'Input dir {self.input_dir} does not exist')

        self.output_dir, backup_dir = utils.prepare_output_dir(output_dir, create_new=False)
        if self.output_dir == self.input_dir:
            self.input_dir = backup_dir  # the input_dir changed to the backup_dir

        self.codebook = utils.load_codebook(codebook)

        print(f'Input directory: {self.input_dir}')
        print(f'Output directory: {self.output_dir}')

        # copy everything from input_dir to output_dir using shutil.copytree except the dataframe
        shutil.copytree(self.input_dir, self.output_dir, ignore=shutil.ignore_patterns(IRR.DATAFRAME_NAME))

        self.df_file = os.path.join(self.input_dir, IRR.DATAFRAME_NAME)
        if not os.path.isfile(self.df_file):
            raise FileNotFoundError(f'Input file {self.df_file} not found')
        self.df = pd.read_csv(self.df_file)
        if len(self.df) == 0:
            raise ValueError(f'Input dataframe is empty')

        # Allow loading older versions of the dataframe with different column name
        if 'prompt_key' in self.df.columns:
            self.df.rename(columns={'prompt_key': IRR.index_cols[1]}, inplace=True)
        if 'prompt_id' in self.df.columns:
            self.df.rename(columns={'prompt_id': IRR.index_cols[1]}, inplace=True)
        if 'rating' in self.df.columns:
            self.df.rename(columns={'rating': IRR.index_cols[2]}, inplace=True)

        index_cols = self.check_present_in_df(self.df, IRR.index_cols)
        self.df.set_index(index_cols, inplace=True)

        # self.df = self.df.replace({True: 'True', False: 'False', 'nan': None, np.nan: None})

        for col in self.df.columns:
            if col in [IRR.col_maj_agree_with_model]:
                continue
            self.df[col] = self.df[col].astype(str)
            self.df[col] = self.df[col].apply(self.convert_to_str)  # TODO check if this is needed

        # print(f'df:\n{self.df}')
        # print(f'df.types: {self.df.dtypes}')
        
        # self.df = self.df.astype('string')

    def __call__(self):
        irr_calculator = IRR(df=self.df, out_dir=self.output_dir)
        irr_results = irr_calculator()

        print(f"Inter-rater reliability results summary:\n{json.dumps(irr_results.get_summary(), indent=2, ensure_ascii=False)}")

        Discourseer.save_output(self.output_dir, irr_results)

    def check_present_in_df(self, df: pd.DataFrame, cols: List[str]) -> List[str]:
        missing_cols = [col for col in cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f'Columns {missing_cols} are missing in the dataframe')
        return cols

    @staticmethod
    def convert_to_str(value):
        # print(f'convert_to_str: {value} ({type(value)})')
        return str(value)
    
        # Convert None to empty string
        if value is None:
            return ''
        
        if isinstance(value, int):
            return str(value)
        # Convert bools to their string representation
        elif isinstance(value, bool):
            return str(value)
        else:
            return str(value)


if __name__ == '__main__':
    main()
