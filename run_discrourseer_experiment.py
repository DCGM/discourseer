from __future__ import annotations
import argparse
import logging
import os
import json
import time
from typing import List

from discourseer.extraction_prompts import ExtractionPrompts
from discourseer.rater import Rater
from discourseer.inter_rater_reliability import IRR
from discourseer.chat_client import ChatClient, Conversation, ChatMessage
from discourseer.utils import pydantic_to_json_file, JSONParser, RatingsCopyMode


def parse_args():
    parser = argparse.ArgumentParser(
        description='Extract answers from text files in a directory using OpenAI GPT-3 and save the results to a file. '
                    'You must have an OpenAI API key to use this script. Specify environment variable OPENAI_API_KEY '
                    'or add it as and argument `--openai-api-key`.')
    parser.add_argument('--texts-dir', type=str, required=True,
                        help='The directory containing the text files to process.')
    parser.add_argument('--ratings-dir', nargs='*', type=str,
                        help='The directory containing the csv files with answer ratings.')
    parser.add_argument('--output-dir', default="data/outputs/test",
                        help='Directory to save the results to.')
    parser.add_argument('--prompt-definitions', default="data/default/prompt_definitions.json")
    parser.add_argument('--prompt-subset', nargs='*',
                        default=list([]),
                        help='The subset to take from file in `prompt-definitions`. '
                             'The accuracy may suffer if there is too many prompts.')
    parser.add_argument('--prompt-schema-definition', default="data/default/prompt_schema_definition.json",
                        help='The file containing the main prompt text + format strings for prompts.')
    parser.add_argument('--copy-input-ratings', choices=[i.name for i in RatingsCopyMode],
                        default=RatingsCopyMode.none, help='Copy input ratings to output folder.')
    parser.add_argument('--openai-api-key', type=str)
    parser.add_argument('--log', default="INFO", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='The logging level to use.')

    return parser.parse_args()


def main():
    args = parse_args()
    log_file = 'data/outputs/logfile.log'
    os.makedirs('data/outputs', exist_ok=True)
    setup_logging(args.log, log_file)
    logging.debug(f"Python file location: {os.path.abspath(__file__)}")
    exit(0)

    discourseer = Discourseer(
        texts_dir=args.texts_dir,
        ratings_dirs=args.ratings_dir,
        output_dir=args.output_dir,
        prompt_definitions=args.prompt_definitions,
        prompt_subset=args.prompt_subset,
        openai_api_key=args.openai_api_key,
        prompt_schema_definition=args.prompt_schema_definition,
        copy_input_ratings=args.copy_input_ratings
    )
    discourseer()

    logging.getLogger().handlers.clear()  # Remove the handlers to avoid logging http connection close
    os.rename(log_file, discourseer.get_output_file(os.path.basename(log_file)))


if __name__ == "__main__":
    main()
