from __future__ import annotations
import argparse
import logging
import os
import json
import time
from typing import List, Union

from discourseer.extraction_prompts import ExtractionPrompts
from discourseer.rater import Rater
from discourseer.inter_rater_reliability import IRR
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
        prompt_definitions=args.prompt_definitions
    )
    calculator()

    # logging.getLogger().handlers.clear()  # Remove the handlers to avoid logging http connection close
    # os.rename(log_file, discourseer.get_output_file(os.path.basename(log_file)))


class Calculator:

    def __init__(self, ratings_dirs: List[str], output_dir: str, prompt_definitions
                 # prompt_subset: List[str] = None,
                 # openai_api_key: str = None, prompt_schema_definition: str = None,
                 # copy_input_ratings: RatingsCopyMode = RatingsCopyMode.none, text_count: int = None
                 ):
        self.output_dir = self.prepare_output_dir(output_dir)
        self.prompts = self.load_prompts(prompt_definitions)
        self.raters = Rater.from_dirs(ratings_dirs, self.prompts)
        # self.input_files = self.get_input_files(experiment_dir, texts_dir, text_count)
        # logging.debug(f"Prompts: {self.prompts}\n\n")
        # self.prompt_schema_definition = self.load_prompt_schema_definition(experiment_dir, prompt_schema_definition)
        # self.copy_input_ratings = copy_input_ratings

        if not self.raters:
            logging.error("No rater files found. Inter-rater reliability will not be calculated.")
            exit(0)

    def __call__(self):
        irr_calculator = IRR(self.raters, out_dir=self.output_dir, calculate_irr_for_options=True)
        irr_results = irr_calculator()
        logging.info(f"Inter-rater reliability results summary:\n{json.dumps(irr_results.get_summary(), indent=2)}")

        utils.pydantic_to_json_file(irr_results, self.get_output_file('irr_results.json'))
        utils.dict_to_json_file(irr_results.get_one_metric('krippendorff_alpha'),
                                self.get_output_file('irr_results_krippendorff_alpha.json'))

    def get_output_file(self, file_name: str):
        return os.path.join(self.output_dir, file_name)

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
