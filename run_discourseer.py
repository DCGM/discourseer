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
from discourseer.chat_client import ChatClient, Conversation, ChatMessage
from discourseer.utils import pydantic_to_json_file, JSONParser, RatingsCopyMode


def parse_args():
    parser = argparse.ArgumentParser(
        description='Extract answers from text files in a directory using OpenAI GPT-3 and save the results to a file. '
                    'You must have an OpenAI API key to use this script. Specify environment variable OPENAI_API_KEY '
                    'or add it as and argument `--openai-api-key`.')

    parser.add_argument('--experiment-dir', type=str,
                        default='experiments/default_experiment',
                        help='Default location of everything necessary for given experiment. Specify different paths '
                             'by using individual arguments. (texts-dir, ratings-dir, output-dir, '
                             'prompt-definitions, prompt-schema-definition).')
    parser.add_argument('--texts-dir', type=str, default=None,
                        help='The directory containing the text files to process.')
    parser.add_argument('--ratings-dir', nargs='*', type=str, default=None,
                        help='The directory containing the csv files with answer ratings.')
    parser.add_argument('--output-dir', default=None,
                        help='Directory to save the results to. Saved to experiment-dir/output if not specified.')
    parser.add_argument('--prompt-schema-definition', default=None,
                        help='JSON file containing GPT connection settings, '
                             'the main prompt text + format strings for prompts.')
    parser.add_argument('--prompt-definitions', default=None,
                        help='JSON file containing the prompt definitions (prompts, question ids, choices...).')

    parser.add_argument('--prompt-subset', nargs='*',
                        default=list([]),
                        help='The subset to take from file in `prompt-definitions`. '
                             'The accuracy may suffer if there is too many prompts.')
    parser.add_argument('--copy-input-ratings', choices=[i.name for i in RatingsCopyMode],
                        default=RatingsCopyMode.none, help='Copy input ratings to output folder.')
    parser.add_argument('--openai-api-key', type=str)
    parser.add_argument('--log', default="INFO", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='The logging level to use.')

    return parser.parse_args()


def setup_logging(log_level: str, log_file: str):
    logging.getLogger().setLevel(log_level)
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(filename)s:%(funcName)s: %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logging.getLogger().addHandler(file_handler)
    logging.getLogger().addHandler(stream_handler)


def main():
    args = parse_args()
    log_file = 'experiments/tmp/logfile.log'
    os.makedirs('experiments/tmp', exist_ok=True)
    setup_logging(args.log, log_file)
    logging.debug(f"Python file location: {os.path.abspath(__file__)}")
    logging.debug(f"Arguments: {args}")

    discourseer = Discourseer(
        experiment_dir=args.experiment_dir,
        texts_dir=args.texts_dir,
        ratings_dirs=args.ratings_dir,
        output_dir=args.output_dir,
        prompt_schema_definition=args.prompt_schema_definition,
        prompt_definitions=args.prompt_definitions,
        prompt_subset=args.prompt_subset,
        copy_input_ratings=args.copy_input_ratings,
        openai_api_key=args.openai_api_key
    )
    discourseer()

    logging.getLogger().handlers.clear()  # Remove the handlers to avoid logging http connection close
    os.rename(log_file, discourseer.get_output_file(os.path.basename(log_file)))


class Discourseer:
    input_ratings_dir = 'input_ratings'

    def __init__(self, experiment_dir: str = 'experiments/default_experiment', texts_dir: str = None,
                 ratings_dirs: List[str] = None, output_dir: str = None, prompt_subset: List[str] = None,
                 prompt_definitions: str = None, openai_api_key: str = None, prompt_schema_definition: str = None,
                 copy_input_ratings: RatingsCopyMode = RatingsCopyMode.none):
        self.input_files = self.get_input_files(experiment_dir, texts_dir)
        self.output_dir = self.prepare_output_dir(experiment_dir, output_dir)
        self.prompts = self.load_prompts(experiment_dir, prompt_definitions, prompt_subset)
        logging.debug(f"Prompts: {self.prompts}\n\n")
        self.raters = self.load_raters(experiment_dir, ratings_dirs, self.prompts)
        self.prompt_schema_definition = self.load_prompt_schema_definition(experiment_dir, prompt_schema_definition)
        self.copy_input_ratings = copy_input_ratings

        if not self.raters:
            logging.warning("No rater files found. Inter-rater reliability will not be calculated.")

        self.conversation_log = self.prompt_schema_definition.model_copy(deep=True)
        end_of_prompt_definition_message = ChatMessage(
            role='assistant', content="This is the end of task definition. The conversation follows.")
        self.conversation_log.messages.append(end_of_prompt_definition_message)

        self.client = ChatClient(openai_api_key=openai_api_key)
        self.model_rater = Rater(name="model", extraction_prompts=self.prompts)

        first_prompt = self.prompt_schema_definition.messages[0].content
        logging.info(f"First prompt: {first_prompt[:min(100, len(first_prompt))]}...")

    def __call__(self):
        for file in self.input_files:
            with open(file, 'r', encoding='utf-8') as f:
                text = f.read()
                response = self.extract_answers(text)
                self.model_rater.add_model_response(os.path.basename(file), response)

        self.model_rater.save_to_csv(self.get_output_file('model_ratings.csv'))
        pydantic_to_json_file(self.conversation_log, self.get_output_file('conversation_log.json'))

        if not self.raters:
            logging.info("No rater files found. Inter-rater reliability will not be calculated.")
            return

        irr_calculator = IRR(self.raters, self.model_rater, self.prompts)
        irr_results = irr_calculator()
        logging.info(f"Inter-rater reliability results:\n{irr_results.model_dump_json(indent=2)}")

        pydantic_to_json_file(irr_results, self.get_output_file('irr_results.json'))
        self.copy_input_ratings_to_output(irr_calculator)

    def extract_answers(self, text):
        logging.debug('New document:\n\n')
        logging.debug(f'Extracting answers from text: {text[:min(50, len(text))]}...')

        conversation = self.prompt_schema_definition.model_copy(deep=True)
        for message in conversation.messages:
            try:
                message.content = message.content.format(**self.prompts.get_format_strings(), text=text)
            except KeyError as e:
                raise KeyError(f"Non-existing format string {e} in message: "
                               f"({message.content[:min(80, len(message.content))]}...")

        response = self.client.invoke(**conversation.model_dump())

        response = response.choices[0].message.content
        response = JSONParser.response_to_dict(response)

        logging.debug(f"Response: {response}")
        self.conversation_log.add_messages(conversation.messages, try_parse_json=True)
        self.conversation_log.messages.append(
            ChatMessage(role="assistant",
                        content=response))

        return response

    def get_output_file(self, file_name: str, input_ratings: bool = False):
        if input_ratings:
            return os.path.join(self.output_dir, self.input_ratings_dir, file_name)
        return os.path.join(self.output_dir, file_name)

    def copy_input_ratings_to_output(self, irr_calculator: IRR):
        if self.copy_input_ratings == RatingsCopyMode.none or not self.raters:
            return

        os.makedirs(os.path.join(self.output_dir, self.input_ratings_dir), exist_ok=True)

        if self.copy_input_ratings == RatingsCopyMode.original.name:
            raters = self.raters
        elif self.copy_input_ratings == RatingsCopyMode.reorganized.name:
            raters_df = irr_calculator.get_reorganized_raters()
            raters = Rater.from_dataframe(raters_df)
        else:
            logging.info(f'Selected copy_input_ratings mode {self.copy_input_ratings} not implemented. Options: '
                         f'{[i.name for i in RatingsCopyMode]}')
            return

        for rater in raters:
            rater.save_to_csv(self.get_output_file(rater.name, input_ratings=True))

    @staticmethod
    def load_prompt_schema_definition(experiment_dir: str, prompt_definition: str = None) -> Conversation:
        if not prompt_definition:
            prompt_definition = Discourseer.find_file_in_experiment_dir(experiment_dir, 'prompt_schema_definition')

        logging.debug(f'Loading prompt definition from file:{prompt_definition}')
        with open(prompt_definition, 'r', encoding='utf-8') as f:
            prompt_definition = json.load(f)

        prompt_definition = Conversation.model_validate(prompt_definition)

        return prompt_definition

    @staticmethod
    def prepare_output_dir(experiment_dir: str, output_dir: str = None) -> str:
        if not output_dir:
            output_dir = os.path.join(experiment_dir, 'output')

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            return output_dir

        output_dir_new = os.path.normpath(output_dir) + time.strftime("_%Y%m%d-%H%M%S")
        os.makedirs(output_dir_new)
        logging.debug(f"Directory {output_dir} already exists. Saving the result to {output_dir_new}")

        return output_dir_new

    @staticmethod
    def get_input_files(experiment_dir: str, texts_dir: str = None) -> List[str]:
        if not texts_dir:
            texts_dir = Discourseer.find_dir_in_experiment_dir(experiment_dir, 'text')

        files = []
        for file in os.listdir(texts_dir):
            if os.path.isfile(os.path.join(texts_dir, file)):
                files.append(os.path.join(texts_dir, file))
        return files

    @staticmethod
    def load_prompts(experiment_dir: str, prompts_file: str = None, prompt_subset: List[str] = None
                     ) -> ExtractionPrompts:
        if not prompts_file:
            prompts_file = Discourseer.find_file_in_experiment_dir(experiment_dir, 'prompt_definitions')

        logging.debug(f'Loading prompts from file: {prompts_file}')
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        prompts = ExtractionPrompts.model_validate(prompts)

        return prompts.select_subset(prompt_subset).select_unique_names_and_question_ids()

    @staticmethod
    def load_raters(experiment_dir: str, ratings_dirs: List[str] = None, prompts: ExtractionPrompts = None) -> List[Rater]:
        if not ratings_dirs:
            ratings_dirs = [Discourseer.find_dir_in_experiment_dir(experiment_dir, 'ratings')]

        return Rater.from_dirs(ratings_dirs, prompts)

    @staticmethod
    def find_dir_in_experiment_dir(experiment_dir: str, dir_name: str) -> Union[str, None]:
        if not os.path.exists(experiment_dir):
            raise FileNotFoundError(f"Experiment directory {experiment_dir} does not exist. "
                                    "Provide it in args or specify all paths individually. "
                                    "(see run_discourseer.py --help)")

        dirs = [path for path in os.listdir(experiment_dir)
                if os.path.isdir(os.path.join(experiment_dir, path)) and dir_name in path]
        dirs.sort()
        if dirs:
            return os.path.join(experiment_dir, dirs[0])

        return None

    @staticmethod
    def find_file_in_experiment_dir(experiment_dir: str, file_name: str) -> Union[str, None]:
        if not os.path.exists(experiment_dir):
            raise FileNotFoundError(f"Experiment directory {experiment_dir} does not exist. "
                                    "Provide it in args or specify all paths individually. "
                                    "(see run_discourseer.py --help)")

        files = [path for path in os.listdir(experiment_dir)
                 if os.path.isfile(os.path.join(experiment_dir, path)) and file_name in path]
        files.sort()
        if files:
            return os.path.join(experiment_dir, files[0])

        return None


if __name__ == "__main__":
    main()
