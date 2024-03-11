from __future__ import annotations
import argparse
import logging
import os
import json
import time
from typing import List

from discourseer.extraction_topics import ExtractionTopics
from discourseer.rater import Rater
from discourseer.inter_rater_reliability import IRR
from discourseer.chat_client import ChatClient, Conversation, ChatMessage
from discourseer.utils import pydantic_to_json_file


def parse_args():
    parser = argparse.ArgumentParser(
        description='Extract topics from text files in a directory using OpenAI GPT-3 and save the results to a file. '
                    'You must have an OpenAI API key to use this script. Specify environment variable OPENAI_API_KEY '
                    'or add it as and argument `--openai-api-key`.')
    parser.add_argument('--texts-dir', type=str, required=True,
                        help='The directory containing the text files to process.')
    parser.add_argument('--ratings-dir', nargs='*', type=str,
                        help='The directory containing the csv files with answer ratings.')
    parser.add_argument('--output-dir', default="data/outputs/test",
                        help='Directory to save the results to.')
    parser.add_argument('--topic-definitions', default="data/default/topic_definitions.json")
    parser.add_argument('--topic-subset', nargs='*',
                        default=list([]),
                        help='The subset to take from file in `topic-definitions`. '
                             'The accuracy may suffer if there is too many topics.')
    parser.add_argument('--prompt-definition', default="data/default/prompt_definition.json",
                        help='The file containing the main prompt text + format strings for topics.')
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
    log_file = 'data/outputs/logfile.log'
    os.makedirs('data/outputs', exist_ok=True)
    setup_logging(args.log, log_file)

    topic_extractor = TopicExtractor(
        texts_dir=args.texts_dir,
        ratings_dirs=args.ratings_dir,
        output_dir=args.output_dir,
        topic_definitions=args.topic_definitions,
        topic_subset=args.topic_subset,
        openai_api_key=args.openai_api_key,
        prompt_definition=args.prompt_definition
    )
    topic_extractor()

    logging.getLogger().handlers.clear()  # Remove the handlers to avoid logging http connection close
    os.rename(log_file, topic_extractor.get_output_file(os.path.basename(log_file)))


class TopicExtractor:
    def __init__(self, texts_dir: str, ratings_dirs: List[str] = None, output_dir: str = 'data/outputs/test',
                 topic_subset: List[str] = None, topic_definitions: str = "data/default/topic_definitions.json",
                 openai_api_key: str = None, prompt_definition: str = "data/default/prompt_definition.json"):
        self.input_files = self.get_input_files(texts_dir)
        self.output_dir, self.output_dir_base = self.prepare_output_dir(output_dir)
        self.topics = self.load_topics(topic_definitions).select_subset(topic_subset)
        self.raters = Rater.from_dirs(ratings_dirs, self.topics)
        self.prompt_definition = self.load_prompt_definition(prompt_definition)

        if not self.raters:
            logging.warning("No rater files found. Inter-rater reliability will not be calculated.")

        self.conversation_log = self.prompt_definition.model_copy(deep=True)
        end_of_prompt_definition_message = ChatMessage(role='assistant', content="Hello!")
        self.conversation_log.messages.append(end_of_prompt_definition_message)

        self.client = ChatClient(openai_api_key=openai_api_key)
        self.model_rater = Rater(name="model", extraction_topics=self.topics)
        # self.system_prompt = self.construct_system_prompt()
        # self.system_prompts = [self.construct_system_prompt(topic) for topic in self.to_extract]
        logging.info(f"First prompt: {self.prompt_definition.messages[0].content}")

    def __call__(self):
        for file in self.input_files:
            with open(file, 'r', encoding='utf-8') as f:
                text = f.read()
                response = self.extract_topics(text)
                self.model_rater.add_model_response(os.path.basename(file), response)

        self.model_rater.save_ratings(self.get_output_file('model_ratings.csv'))
        pydantic_to_json_file(self.conversation_log, self.get_output_file('conversation_log.json'))

        if self.raters:
            irr_results = IRR(self.raters, self.model_rater, self.topics)()
            logging.info(f"Inter-rater reliability results:\n{irr_results.model_dump_json(indent=2)}")
            pydantic_to_json_file(irr_results, self.get_output_file('irr_results.json'))

    def extract_topics(self, text):
        logging.debug('\n\n')
        logging.debug(f'Extracting topics from text: {text[:min(50, len(text))]}...')

        conversation = self.prompt_definition.model_copy(deep=True)
        for message in conversation.messages:
            message.content = message.content.format(**self.topics.get_format_strings(), text=text)

        response = self.client.invoke(**conversation.dict())

        response = json.loads(response.choices[0].message.content)
        logging.debug(f"Response: {response}")
        self.conversation_log.messages += conversation.messages
        self.conversation_log.messages.append(
            ChatMessage(role="assistant",
                        content=json.dumps(response, indent=2, ensure_ascii=False)))

        return response

    def get_output_file(self, file_name: str):
        file, ext = os.path.splitext(file_name)
        return os.path.join(self.output_dir, f'{file}{ext}')
        # return os.path.join(self.output_dir, f'{file}_{self.output_dir_base}{ext}')

    @staticmethod
    def load_prompt_definition(prompt_definition: str):
        logging.debug(f'Loading prompt definition from file:{prompt_definition}')
        with open(prompt_definition, 'r', encoding='utf-8') as f:
            prompt_definition = json.load(f)

        prompt_definition = Conversation.model_validate(prompt_definition)

        return prompt_definition

    @staticmethod
    def prepare_output_dir(output_dir: str) -> tuple[str, str]:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            return output_dir, os.path.basename(os.path.normpath(output_dir))

        output_dir_new = os.path.normpath(output_dir) + time.strftime("_%Y%m%d-%H%M%S")
        os.makedirs(output_dir_new)
        logging.debug(f"Directory {output_dir} already exists. Saving the result to {output_dir_new}")

        return output_dir_new, os.path.basename(output_dir_new)

    @staticmethod
    def get_input_files(texts_dir: str):
        files = []
        for file in os.listdir(texts_dir):
            if os.path.isfile(os.path.join(texts_dir, file)):
                files.append(os.path.join(texts_dir, file))
        return files

    @staticmethod
    def load_topics(topics_file: str):
        logging.debug(f'Loading topics from file:{topics_file}')
        with open(topics_file, 'r', encoding='utf-8') as f:
            topics = json.load(f)

        return ExtractionTopics.model_validate(topics)


if __name__ == "__main__":
    main()
