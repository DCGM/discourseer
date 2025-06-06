from __future__ import annotations
import argparse
import logging
import os
import json
import time
from typing import List, Union
from tqdm import tqdm

from discourseer.codebook import Codebook, all_questions_at_once_tag
from discourseer.rater import Rater
from discourseer.inter_rater_reliability import IRR
from discourseer.chat_client import ChatClient, Conversation, ChatMessage, LogChatMessage, ConversationLog
from discourseer import utils
from discourseer.utils import pydantic_to_json_file, JSONParser, RatingsCopyMode
from discourseer.visualize_IRR import visualize_results


def parse_args():
    parser = argparse.ArgumentParser(
        description='Extract answers from text files in a directory using OpenAI GPT-3 and save the results to a file. '
                    'You must have an OpenAI API key to use this script. Specify environment variable OPENAI_API_KEY '
                    'or add it as and argument `--openai-api-key`.')

    parser.add_argument('--experiment-dir', type=str,
                        default='experiments/default_experiment',
                        help='Default location of everything necessary for given experiment. Specify different paths '
                             'by using individual arguments. (texts-dir, ratings-dir, output-dir, '
                             'codebook, prompt-schema-definition).')
    parser.add_argument('--texts-dir', type=str, default=None,
                        help='The directory containing the text files to process.')
    parser.add_argument('--ratings-dir', nargs='*', type=str, default=None,
                        help='The directory containing the csv files with answer ratings.')
    parser.add_argument('--output-dir', default=None,
                        help='Directory to save the results to. Saved to experiment-dir/output if not specified.')
    parser.add_argument('--prompt-schema-definition', default=None,
                        help='JSON file containing GPT connection settings, '
                             'the main prompt text + format strings for prompts.')
    parser.add_argument('--codebook', default=None,
                        help='JSON file containing the codebook (codebok name+version, questions, options...).')

    parser.add_argument('--question-subset', nargs='*', default=list([]),
                        help='The subset to take from file in `codebook`. If not specified, all questions in the codebook are used.')
    parser.add_argument('--text-count', type=int, default=None,
                        help='Number of texts to process (for testing, you can use only few texts).')
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

    # suppress logs from specific libraries
    for lib in ['httpx', 'httpcore', 'openai', 'matplotlib']:
        logger = logging.getLogger(lib)
        logger.setLevel(logging.WARNING)


def main():
    args = parse_args()

    tmp_dir = 'tmp'
    log_file = os.path.join(tmp_dir, 'logfile.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    if os.path.exists(log_file):
        os.remove(log_file)

    setup_logging(args.log, log_file)
    logging.debug(f"Python file location: {os.path.abspath(__file__)}")
    logging.debug(f"Arguments: {args}")

    discourseer = Discourseer(
        experiment_dir=args.experiment_dir,
        texts_dir=args.texts_dir,
        ratings_dirs=args.ratings_dir,
        output_dir=args.output_dir,
        prompt_schema_definition=args.prompt_schema_definition,
        codebook=args.codebook,
        question_subset=args.question_subset,
        text_count=args.text_count,
        copy_input_ratings=args.copy_input_ratings,
        openai_api_key=args.openai_api_key
    )
    discourseer()

    logging.getLogger().handlers.clear()  # Remove the handlers to avoid logging http connection close
    os.rename(log_file, discourseer.get_output_file(os.path.basename(log_file)))
    os.rmdir(tmp_dir)


class Discourseer:
    input_ratings_dir = 'input_ratings'

    def __init__(self, experiment_dir: str = 'experiments/default_experiment', texts_dir: str = None,
                 ratings_dirs: List[str] = None, output_dir: str = None, question_subset: List[str] = None,
                 codebook: str = None, openai_api_key: str = None, prompt_schema_definition: str = None,
                 copy_input_ratings: RatingsCopyMode = RatingsCopyMode.none, text_count: int = None):
        self.input_files = self.get_input_files(experiment_dir, texts_dir, text_count)
        self.output_dir = self.prepare_output_dir(experiment_dir, output_dir)
        self.codebook = self.load_codebook(experiment_dir, codebook, question_subset)
        self.raters = self.load_raters(experiment_dir, ratings_dirs, self.codebook)
        self.prompt_schema_definition = self.load_prompt_schema_definition(experiment_dir, prompt_schema_definition)
        self.copy_input_ratings = copy_input_ratings

        if getattr(self.prompt_schema_definition, 'prompt_individual_questions', False):
            self.individual_codebooks = self.codebook.split_by_individual_questions()
        else:
            self.individual_codebooks = [self.codebook]

        if not self.raters:
            logging.warning("No rater files found. Inter-rater reliability will not be calculated.")

        conversation_setting = self.prompt_schema_definition.model_dump()
        conversation_setting.pop('messages', None)
        self.conversation_log = ConversationLog(schema_definition=self.prompt_schema_definition.messages, messages=[], chat_log=[], **conversation_setting)

        self.client = ChatClient(openai_api_key=openai_api_key)
        self.model_rater = Rater(name="model", codebook=self.codebook)

        first_prompt = self.prompt_schema_definition.messages[0].content
        logging.info(f"First prompt: {first_prompt[:min(100, len(first_prompt))]}...")

    def __call__(self):
        logging.info(f'Processing {len(self.input_files)} texts with {len(self.individual_codebooks)} codebook(s).')
        for file_counter, file in enumerate(tqdm(self.input_files)):
            for codebook in self.individual_codebooks:
                with open(file, 'r', encoding='utf-8') as f:
                    text = f.read()
                    logging.debug(f'New document {file_counter + 1}/{len(self.input_files)}: {os.path.basename(file)}\n\n')
                    response = self.extract_answers(text, os.path.basename(file), codebook)
                    self.model_rater.add_model_response(os.path.basename(file), response)
            pydantic_to_json_file(self.conversation_log, self.get_output_file('conversation_log.json'), exclude=['messages'], exclude_none=True)
            self.model_rater.save_to_csv(self.get_output_file('model_ratings.csv'))
            self.model_rater.save_unmatched_responses(self.get_output_file('unmatched_model_responses.json'))
            self.model_rater.save_to_spreadsheet(self.get_output_file('model_ratings_spreadsheet.csv'))

        if not self.raters:
            logging.info("No rater files found. Inter-rater reliability will not be calculated.")
            return

        irr_calculator = IRR(raters=self.raters, model_rater=self.model_rater, out_dir=self.output_dir,
                             export_majority_agreement_files_and_questions=True)

        self.save_output(self.output_dir, irr_calculator)
        self.copy_input_ratings_to_output(irr_calculator)

    def extract_answers(self, text: str, text_id: str, codebook: Codebook):
        text_short = text[:min(40, len(text))].replace('\n', '')
        question_message = "" if len(codebook.questions) > 1 else f"for question: {codebook.questions[0].id}"
        logging.info(f"Extracting answers from text: {text_id} ({text_short}...) {question_message}")

        conversation = self.prompt_schema_definition.model_copy(deep=True)
        for message in conversation.messages:
            codebook.check_correct_usage_of_format_strings(message.content)
            try:
                message.content = message.content.format(**codebook.get_format_strings(), text=text)
            except KeyError as e:
                raise KeyError(f"Non-existing format string {e} in message: "
                               f"({message.content[:min(80, len(message.content))]}...")

        conversation = self.client.ensure_maximal_length(conversation)
        response = self.client.invoke(**conversation.model_dump())

        logging.debug(f"Response raw: {response}")
        response = response.choices[0].message.content
        if response == '':
            logging.warning(f"Empty response from GPT model for text: {text_id}. Possible cause is "
                            f"not enough output tokens. Consider raising max_tokens/max_completion_tokens parameter"
                            f" especially if using an o series reasoning model like o1 or o3")
        response = JSONParser.response_to_dict(response)

        logging.debug(f"Response: {response}")
        if len(codebook.questions) > 1:
            question_id = all_questions_at_once_tag
        else:
            question_id = codebook.questions[0].id

        log_chat_message = LogChatMessage(
            text_id=text_id,
            question_id=question_id,
            messages=conversation.messages + [ChatMessage(role="assistant", content=response)])
        self.conversation_log.chat_log.append(log_chat_message)

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
    def save_output(output_dir: str, irr_calculator: IRR):
        logging.info(irr_calculator.get_maj_agg_files_and_questions_summary())

        irr_results = irr_calculator()

        logging.info(f"Inter-rater reliability results summary:\n{json.dumps(irr_results.get_summary(), indent=2, ensure_ascii=False)}")
        pydantic_to_json_file(irr_results, os.path.join(output_dir, 'irr_results.json'), exclude_none=True)
        visualize_results(irr_results, os.path.join(output_dir, 'irr_results.png'))

        # model_rater.save_to_csv(os.path.join(output_dir, 'model_ratings.csv'))
        # model_rater.save_unmatched_responses(os.path.join(output_dir, 'unmatched_model_responses.json'))
        # model_rater.save_to_spreadsheet(os.path.join(output_dir, 'model_ratings_spreadsheet.csv'))

    @staticmethod
    def load_prompt_schema_definition(experiment_dir: str, prompt_schema: str = None) -> Conversation:
        if not prompt_schema:
            prompt_schema = Discourseer.find_file_in_experiment_dir(experiment_dir, 'prompt_schema_definition')

        logging.info(f'Loading prompt schema definition from file:{prompt_schema}')
        with open(prompt_schema, 'r', encoding='utf-8') as f:
            prompt_schema = json.load(f)

        prompt_schema = Conversation.model_validate(prompt_schema)

        return prompt_schema

    @staticmethod
    def prepare_output_dir(experiment_dir: str, output_dir: str = None) -> str:
        if not output_dir:
            output_dir = os.path.join(experiment_dir, 'output')
        output_dir, _ = utils.prepare_output_dir(output_dir, create_new=True)

        return output_dir

    @staticmethod
    def get_input_files(experiment_dir: str, texts_dir: str = None, text_count: int = None) -> List[str]:
        if not texts_dir:
            texts_dir = Discourseer.find_dir_in_experiment_dir(experiment_dir, 'text')

        files = []
        for file in os.listdir(texts_dir):
            if os.path.isfile(os.path.join(texts_dir, file)):
                files.append(os.path.join(texts_dir, file))

        if text_count:
            files = files[:min(text_count, len(files))]

        return files

    @staticmethod
    def load_codebook(experiment_dir: str, codebook_file: str = None, question_subset: List[str] = None
                     ) -> Codebook:
        if not codebook_file:
            codebook_file = Discourseer.find_file_in_experiment_dir(experiment_dir, 'codebook')

        codebook = utils.load_codebook(codebook_file, question_subset)
        return codebook

    @staticmethod
    def load_raters(experiment_dir: str, ratings_dirs: List[str] = None, codebook: Codebook = None) -> List[Rater]:
        if not ratings_dirs:
            ratings_dirs = [Discourseer.find_dir_in_experiment_dir(experiment_dir, 'rating')]

        return Rater.from_dirs(ratings_dirs, codebook)

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
            if len(files) > 1:
                raise FileExistsError(f"Multiple files with name {file_name} found in {experiment_dir}. "
                                      f"Specify the file with corresponding argument. (see run_discourseer.py --help)")
            return os.path.join(experiment_dir, files[0])

        return None


if __name__ == "__main__":
    main()
