from __future__ import annotations
import argparse
import logging
import os
import json
import time
from typing import List

import openai
from openai import OpenAI
import backoff

from discourseer.extraction_prompts import extraction_prompts
from discourseer.rater import Rater
from discourseer.inter_rater_reliability import IRR


def parse_args():
    parser = argparse.ArgumentParser(
        description='Extract topics from text files in a directory using OpenAI GPT-3 and save the results to a file."'
                    ' You must have an OpenAI API key to use this script. Specify environment variable OPENAI_API_KEY.')
    parser.add_argument('--texts-dir', type=str, required=True,
                        help='The directory containing the text files to process.')
    parser.add_argument('--ratings-dir', nargs='*', type=str,
                        help='The directory containing the csv files with answer ratings.')
    parser.add_argument('--output-file', default="result.csv",
                        help='The file to save the results to.')
    parser.add_argument('--extract', nargs='*', choices=extraction_prompts.keys(),
                        default=list(["5-range", "6-genre", "8-message-trigger", "9-place"]),
                        help='The types of extractions to perform. '
                             'The accuracy may suffer if you select too many types.')
    parser.add_argument('--log', default="INFO", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='The logging level to use.')

    return parser.parse_args()


def main():
    args = parse_args()
    logger = logging.getLogger()
    logger.setLevel(args.log)

    topic_extractor = TopicExtractor(
        texts_dir=args.texts_dir,
        ratings_dir=args.ratings_dir,
        output_file=args.output_file,
        extract=args.extract
    )
    topic_extractor()


class TopicExtractor:
    def __init__(self, texts_dir: str, ratings_dir: List[str] = None, output_file: str = 'result.csv',
                 extract: List[str] = None):
        self.input_files = self.get_input_files(texts_dir)
        # self.ratings_dir = ratings_dir if ratings_dir else []
        self.output_file = self.prepare_output_file(output_file)
        self.extract = extract if extract else list(extraction_prompts.keys())
        self.raters = Rater.from_dirs(ratings_dir)
        if not self.raters:
            logging.warning("No rater files found. Inter-rater reliability will not be calculated.")

        self.client = OpenAI()
        self.model_rater = Rater(name="model")
        self.system_prompt = self.construct_system_prompt()
        # self.system_prompts = [self.construct_system_prompt(topic) for topic in self.to_extract]
        logging.info(f"System prompt: {self.system_prompt}")

    def __call__(self):
        for file in self.input_files:
            with open(file, 'r', encoding='utf-8') as f:
                text = f.read()
                response = self.extract_topics(text)
                self.model_rater.add_model_response(os.path.basename(file), response)

        self.model_rater.save_ratings(self.output_file)

        if self.raters:
            irr_results = IRR(self.raters, self.model_rater)()
            logging.info(f"Inter-rater reliability results:\n{json.dumps(irr_results, indent=2)}")

    def construct_system_prompt(self):
        prompt = "You are a media content analyst. You are analyzing the following text to extract "
        prompt += ", ".join([extraction_prompts[topic].name for topic in self.extract]) + ". "
        prompt += " ".join(extraction_prompts[topic].get_description() for topic in self.extract) + " "
        prompt += "You will provide lists of the identified " + ", ".join([extraction_prompts[topic].name
                                                                           for topic in self.extract])
        prompt += " as a JSON object with keys: " + ", ".join(self.extract) + "."
        prompt += f" Text will be in Czech language."
        return prompt

    def extract_topics(self, text):
        logging.debug('\n\n')
        logging.debug(f'Extracting topics from text: {text[:min(50, len(text))]}')

        response = self.completions_with_backoff(
            model="gpt-3.5-turbo-0125",
            messages=[
                {
                    "role": "system",
                    "content": self.system_prompt
                },
                {
                    "role": "user",
                    "content": "The text to analyze is: " + text
                }
            ],
            max_tokens=1024,
            temperature=0.0,
            top_p=0,
            response_format={"type": "json_object"}
        )
        response = json.loads(response.choices[0].message.content)
        logging.debug(f"Response: {response}")
        return response

    @backoff.on_exception(backoff.expo, openai.RateLimitError)
    def completions_with_backoff(self, **kwargs):
        return self.client.chat.completions.create(**kwargs)

    @staticmethod
    def prepare_output_file(output_file: str):
        path_location = os.path.dirname(output_file)
        if not os.path.exists(path_location):
            os.makedirs(path_location)

        file_name = os.path.splitext(os.path.basename(output_file))[0]
        if os.path.exists(output_file):
            file_name += time.strftime("_%Y%m%d-%H%M%S")
            logging.debug(f"File {output_file} already exists. Saving the result to {file_name}.csv")
        output_file = os.path.join(path_location, file_name + ".csv")

        return output_file

    @staticmethod
    def get_input_files(texts_dir: str):
        files = []
        for file in os.listdir(texts_dir):
            if os.path.isfile(os.path.join(texts_dir, file)):
                files.append(os.path.join(texts_dir, file))
        return files


if __name__ == "__main__":
    main()
