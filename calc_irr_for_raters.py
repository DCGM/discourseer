from __future__ import annotations
import argparse
import logging
import os
import json
import time
from typing import List, Union, Dict

import matplotlib.pyplot as plt
import pandas as pd
from irrCAC.raw import CAC

from discourseer.extraction_prompts import ExtractionPrompts
from discourseer.rater import Rater
from discourseer.inter_rater_reliability import IRR
from discourseer.visualize_IRR import visualize_irr_results_only_human_raters
from discourseer import utils


def parse_args():
    parser = argparse.ArgumentParser(
        description='Load ratings from csv files and calculate inter-rater reliability.')

    parser.add_argument('--ratings-dir', nargs='*', type=str,
                        help='The directory containing the csv files with answer ratings.')
    parser.add_argument('--output-dir',
                        help='Directory to save the results to.')
    parser.add_argument('--prompt-definitions', default=None,
                        help='JSON file containing the prompt definitions (prompts, question ids, choices...).')
    parser.add_argument('--threshold', type=float, default=0.6,
                        help='The threshold for IRR of a question to be considered acceptable.')
    parser.add_argument('--metric', default='krippendorff_alpha', choices=['krippendorff_alpha', 'gwet_ac1', 'fleiss_kappa'],
                        help='The main metric to take into account for acceptable questions and visualization.')

    # parser.add_argument('--log', default="INFO", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
    #                     help='The logging level to use.')

    return parser.parse_args()


# def setup_logging(log_level: str, log_file: str):
#     logging.getLogger().setLevel(log_level)
#     formatter = logging.Formatter('%(levelname)s:%(name)s:%(filename)s:%(funcName)s: %(message)s')
#
#     stream_handler = logging.StreamHandler()
#     stream_handler.setLevel(log_level)
#     stream_handler.setFormatter(formatter)
#     file_handler = logging.FileHandler(log_file)
#     file_handler.setLevel(logging.DEBUG)
#     file_handler.setFormatter(formatter)
#
#     logging.getLogger().addHandler(file_handler)
#     logging.getLogger().addHandler(stream_handler)


def main():
    args = parse_args()
    # log_file = 'experiments/tmp/logfile.log'
    # os.makedirs('experiments/tmp', exist_ok=True)
    # setup_logging(args.log, log_file)
    # logging.debug(f"Python file location: {os.path.abspath(__file__)}")
    print(f"Arguments: {args}")

    calculator = Calculator(
        ratings_dirs=args.ratings_dir,
        output_dir=args.output_dir,
        prompt_definitions=args.prompt_definitions,
        threshold=args.threshold,
        metric=args.metric
    )
    calculator()

    # logging.getLogger().handlers.clear()  # Remove the handlers to avoid logging http connection close
    # os.rename(log_file, discourseer.get_output_file(os.path.basename(log_file)))


class Calculator:

    def __init__(self, ratings_dirs: List[str], output_dir: str, prompt_definitions, threshold: float = 0.6, metric: str = 'krippendorff_alpha',
                 # prompt_subset: List[str] = None,
                 # openai_api_key: str = None, prompt_schema_definition: str = None,
                 # copy_input_ratings: RatingsCopyMode = RatingsCopyMode.none, text_count: int = None
                 ):
        self.output_dir = self.prepare_output_dir(output_dir)
        self.prompts = self.load_prompts(prompt_definitions)
        self.raters = Rater.from_dirs(ratings_dirs, self.prompts)
        self.threshold = threshold
        self.metric = metric
        # self.input_files = self.get_input_files(experiment_dir, texts_dir, text_count)
        # logging.debug(f"Prompts: {self.prompts}\n\n")
        # self.prompt_schema_definition = self.load_prompt_schema_definition(experiment_dir, prompt_schema_definition)
        # self.copy_input_ratings = copy_input_ratings

        if not self.raters:
            logging.error("No rater files found. Inter-rater reliability will not be calculated.")
            exit(0)

    def __call__(self):
        self.irr_calculator = IRR(self.raters, out_dir=self.output_dir, calculate_irr_for_options=True)
        irr_results = self.irr_calculator()
        logging.info(f"Inter-rater reliability results summary:\n{json.dumps(irr_results.get_summary(), indent=2)}")

        utils.pydantic_to_json_file(irr_results, self.get_output_file('irr_results.json'))
        utils.dict_to_json_file(irr_results.get_one_metric_and_variant(self.metric, 'without_model'),
                                self.get_output_file(f'irr_results_{self.metric}.json'))

        visualize_irr_results_only_human_raters(irr_results, location=self.get_output_file(f'irr_results_{self.metric}.png'), metric=self.metric)

        self.analyze_acceptable_questions(irr_results, metric=self.metric)

        self.export_prompt_option_results()

    def get_output_file(self, file_name: str):
        return os.path.join(self.output_dir, file_name)

    def export_prompt_option_results(self):
        input_dir = self.irr_calculator.out_prompts_and_options_dir

        if not os.path.isdir(input_dir):
            raise ValueError(f'Input {input_dir} for export_prompt_option_results does not exist or is not a folder.')

        out_dirname = input_dir + '_exported'
        os.makedirs(out_dirname, exist_ok=True)

        # results_file = 'results.json'
        results = {'kripp': [], 'gwet': []}

        for file in os.listdir(input_dir):
            if not file.endswith('.csv') or not os.path.isfile(os.path.join(input_dir, file)):
                continue

            file_path = os.path.join(input_dir, file)
            out_file_name = os.path.join(out_dirname, file)

            # print(f'\nLoading dataframe from {file_path}')
            df = pd.read_csv(file_path)
            if 'rating' in df.columns:
                df.set_index(['file', 'rating'], inplace=True)
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

        # print(f'\nResults[kripp]: {results["kripp"]}')
        # json.dump(results, open(results_file, 'w'), indent=2)

        # promitni krippendorff z rozsahu -1 až 1 na 0 až 1
        # results['kripp'] = [(k + 1) / 2 for k in results['kripp']]

        plt.scatter(results['kripp'], results['gwet'], alpha=0.5)
        plt.xlabel('Krippendorff alpha (-1 až 1)')
        plt.ylabel('Gwet AC1 (0 až 1)')
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dirname, 'results_scatter.png'))
        plt.clf()

    def analyze_acceptable_questions(self, results: IRR, metric: str = 'krippendorff_alpha') -> Dict[str, float]:
        all_questions = results.to_dict_of_results_of_metric_and_variant(metric, 'without_model')
        acceptable_questions = {k: v for k, v in all_questions.items() if v >= self.threshold}

        acceptable_questions_names = [q for q in acceptable_questions.keys() 
                                      if q not in ['overall', 'mean_through_prompts']]
        acceptable_questions_names = ' '.join(acceptable_questions_names)

        print(f"Acceptable questions ({len(acceptable_questions)} out of {len(all_questions)} >= {self.threshold}):")
        print(f"{acceptable_questions_names}")
        print(f"{json.dumps(acceptable_questions, indent=2)}")

        utils.dict_to_json_file(acceptable_questions, self.get_output_file(f'acceptable_questions_{metric}.json'))
        # save list(acceptable_questions.keys()) to a txt file
        with open(self.get_output_file(f'acceptable_questions_{metric}.txt'), 'w') as f:
            f.write(acceptable_questions_names + '\n')

    @staticmethod
    def prepare_output_dir(output_dir: str = None) -> str:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            return output_dir

        output_dir_new = os.path.normpath(output_dir) + time.strftime("_%Y%m%d-%H%M%S")
        os.makedirs(output_dir_new)
        logging.debug(f"Directory {output_dir} already exists. Saving the result to {output_dir_new}")

        return output_dir_new

    @staticmethod
    def load_prompts(prompts_file: str = None) -> ExtractionPrompts:

        logging.debug(f'Loading prompts from file: {prompts_file}')
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        prompts = ExtractionPrompts.model_validate(prompts)

        return prompts.select_unique_names_and_question_ids()


if __name__ == "__main__":
    main()
