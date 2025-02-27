from __future__ import annotations
import argparse
import logging
import os
import json
from typing import List, Union, Dict

import matplotlib.pyplot as plt
import pandas as pd
from irrCAC.raw import CAC

from discourseer.rater import Rater
from discourseer.inter_rater_reliability import IRR
from discourseer.visualize_IRR import visualize_irr_results_only_human_raters
from discourseer import utils


def parse_args():
    parser = argparse.ArgumentParser(
        description='Load ratings from csv files and calculate inter-rater reliability.')

    parser.add_argument('--ratings-dir', nargs='*', type=str,
                        help='The directory containing the csv files with answer ratings.')
    parser.add_argument('--output-dir', type=str, default='output_IRR',
                        help='Directory to save the results to.')
    parser.add_argument('--codebook', default=None,
                        help='JSON file containing the codebook (codebok name+version, questions, options...).')
    parser.add_argument('--thresholds', type=float, nargs='*', default=[0.8, 0.6],
                        help='The thresholds for IRR of a question to be considered acceptable.')
    parser.add_argument('--metric', default='krippendorff_alpha', choices=['krippendorff_alpha', 'gwet_ac1', 'fleiss_kappa'],
                        help='The main metric to take into account for acceptable questions and visualization.')

    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Arguments: {args}")

    calculator = Calculator(
        ratings_dirs=args.ratings_dir,
        output_dir=args.output_dir,
        codebook=args.codebook,
        thresholds=args.thresholds,
        metric=args.metric
    )
    calculator()


class Calculator:

    def __init__(self, ratings_dirs: List[str], codebook, output_dir: str = 'output_IRR', metric: str = 'krippendorff_alpha',
                 thresholds: List[float] = [0.8, 0.6]):
        self.output_dir, _ = utils.prepare_output_dir(output_dir)
        self.codebook = utils.load_codebook(codebook)
        self.raters = Rater.from_dirs(ratings_dirs, self.codebook)
        self.thresholds = thresholds
        self.metric = metric

        if not self.raters:
            logging.error("No rater files found. Inter-rater reliability will not be calculated.")
            exit(0)
        
        self.irr_calculator = None

    def __call__(self):
        self.irr_calculator = IRR(self.raters, out_dir=self.output_dir)
        irr_results = self.irr_calculator()
        logging.info(f"Inter-rater reliability results summary:\n{json.dumps(irr_results.get_summary(), indent=2, ensure_ascii=False)}")

        utils.pydantic_to_json_file(irr_results, self.get_output_file('irr_results.json'))
        utils.dict_to_json_file(irr_results.get_one_metric_and_variant(self.metric, 'without_model'),
                                self.get_output_file(f'irr_results_{self.metric}.json'))

        visualize_irr_results_only_human_raters(irr_results, location=self.get_output_file(f'irr_results_{self.metric}.png'), metric=self.metric, thresholds=self.thresholds)

        print('')
        for threshold in self.thresholds:
            self.analyze_acceptable_questions(irr_results, metric=self.metric, threshold=threshold)
            print('')

        self.export_question_option_results()

    def get_output_file(self, file_name: str):
        return os.path.join(self.output_dir, file_name)

    def export_question_option_results(self):
        input_dir = self.irr_calculator.out_questions_and_options_dir

        if not os.path.isdir(input_dir):
            raise ValueError(f'Input {input_dir} for export_question_option_results does not exist or is not a folder.')

        out_dirname = input_dir + '_exported'
        os.makedirs(out_dirname, exist_ok=True)

        # results_file = 'results.json'
        results = {'kripp': [], 'gwet': []}

        for file in os.listdir(input_dir):
            if not file.startswith('dataframe__') or not file.endswith('.csv') or not os.path.isfile(os.path.join(input_dir, file)):
                continue

            file_path = os.path.join(input_dir, file)
            out_file_name = os.path.join(out_dirname, file)

            # print(f'\nLoading dataframe from {file_path}')
            df = pd.read_csv(file_path)
            if 'option_id' in df.columns:
                df.set_index(['file', 'option_id'], inplace=True)
            else:
                df.set_index('file', inplace=True)

            df = df.drop(columns=['majority', 'worst_case'])
            df.replace({True: '1', False: '0'}, inplace=True)
            df.fillna('', inplace=True)
            df = df.astype(str)

            cac = CAC(df)
            results['kripp'].append(IRR.get_cac_metric(cac, 'krippendorff'))
            # print(f'Krippendorff\'s alpha for this dataframe is: {results["kripp"][-1]}')

            results['gwet'].append(IRR.get_cac_metric(cac, 'gwet'))
            # print(f'Gwet\'s AC1 for this dataframe is: {results["gwet"][-1]}')

            # save_to_export(df, input_file=input_dir)
            df.to_csv(out_file_name, header=False, index=False)

        plt.scatter(results['kripp'], results['gwet'], alpha=0.5)
        plt.xlabel('Krippendorff alpha (-1 až 1)')
        plt.ylabel('Gwet AC1 (0 až 1)')
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'results_scatter.png'))
        plt.clf()

    def analyze_acceptable_questions(self, results: IRR, metric: str = 'krippendorff_alpha', threshold: float = 0.8):
        all_questions = results.to_dict_of_results_of_metric_and_variant(metric, 'without_model')
        acceptable_questions = {question_id: v for question_id, v in all_questions.items() if v >= threshold}

        acceptable_questions_ids = [question_id for question_id in acceptable_questions.keys()
                                      if question_id not in ['overall', 'mean_through_questions']]
        acceptable_questions_ids = ' '.join(acceptable_questions_ids)

        print(f"For threshold {threshold} there are ({len(acceptable_questions)} out of {len(all_questions)}) acceptable questions:")
        if acceptable_questions:
            print(f"{acceptable_questions_ids}")
            print(f"{json.dumps(acceptable_questions, indent=2, ensure_ascii=False)}")
        else:
            print(f"No acceptable questions found")

        utils.dict_to_json_file(acceptable_questions, self.get_output_file(f'acceptable_questions_{metric}_{threshold}.json'))

        with open(self.get_output_file(f'acceptable_questions_{metric}_{threshold}.txt'), 'w') as f:
            f.write(acceptable_questions_ids + '\n')



if __name__ == "__main__":
    main()
