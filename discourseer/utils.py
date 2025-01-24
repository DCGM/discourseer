import json
import pydantic
import re
import os
import logging
from enum import Enum
from typing import Dict, List, Tuple
import time

from discourseer.codebook import Codebook

logger = logging.getLogger()


class RatingsCopyMode(Enum):
    none = "none"
    original = "original"
    reorganized = "reorganized"

def result_dataframe_index_columns():
    return ['file', 'question_id', 'rating']

def pydantic_to_json_file(model: pydantic.BaseModel, file_path: str, exclude: list[str] = None):
    model_dump = model.model_dump(exclude=exclude)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(model_dump, f, ensure_ascii=False, indent=2)


def dict_to_json_file(data: dict, file_path: str):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def json_file_to_pydantic(file_path: str, cls):
    if not issubclass(cls, pydantic.BaseModel):
        raise ValueError(f"Class {cls} is not a subclass of pydantic.BaseModel")
    if not os.path.exists(file_path) and not os.path.isfile(file_path):
        raise FileNotFoundError(f"File {file_path} not found.")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return cls.model_validate(data)


def individual_option_irr_to_csv(results: Dict[str, Dict[str, float]], file_path: str):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('question,option,irr\n')
        for question, options in results.items():
            for option, irr in options.items():
                f.write(f'{question},{option},{irr}\n')


def prepare_output_dir(output_dir: str = None, create_new: bool = True) -> Tuple[str, str]:
    # create_new False is used in calc_irr_for_dataframe.py, where the input_dir is copied to output_dir, so we don't want to create a new output_dir
    if not os.path.exists(output_dir):
        if create_new:
            os.makedirs(output_dir)
        return output_dir, None

    backup_dir = os.path.normpath(output_dir) + '_backup_' + time.strftime("%Y%m%d-%H%M%S")
    os.rename(output_dir, backup_dir)

    if create_new:
        os.makedirs(output_dir)
    logging.debug(f"Directory {output_dir} already existed. Saving backup to {backup_dir}. New output will be saved in {output_dir}")

    return output_dir, backup_dir


def load_codebook(codebook_file: str = None, question_subset: List[str] = None
                 ) -> Codebook:
    logging.debug(f'Loading codebook from file: {codebook_file}')

    if not os.path.exists(codebook_file):
        raise FileNotFoundError(f"File {codebook_file} not found.")

    with open(codebook_file, 'r', encoding='utf-8') as f:
        codebook_json = json.load(f)

    try:
        codebook = Codebook.model_validate(codebook_json)
    except pydantic.ValidationError as e:
        raise ValueError(f"Failed to validate codebook from file {codebook_file}. Error: {e}")
    logging.debug(f"Loaded codebook: {codebook.codebook_name} (verze: {codebook.codebook_version})")

    orig_question_ids = set([q.id for q in codebook.questions])

    codebook.select_subset(question_subset).select_unique_names()

    if len(codebook.questions) == 0:
        raise ValueError(f"No questions selected from question_subset {question_subset}. "
                          "Check the question_subset argument and use one or more of the following: "
                          f"{', '.join(orig_question_ids)}")

    return codebook


class JSONParser:
    @staticmethod
    def try_parse_json(json_str: str) -> dict | None:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def response_to_dict(response: str | dict) -> dict:
        response_orig = response
        if isinstance(response, dict):
            return response

        result = JSONParser.try_parse_json(response)
        if result:
            return result

        # try to parse response from Markdown code block
        response = JSONParser.from_markdown_code_block(response)
        result = JSONParser.try_parse_json(response)
        if result:
            return result

        logger.error(f"Failed to parse response to json. "
                     f"Original response:\n{response_orig}\nPartly parsed response:\n{response}")

        return {}

    @staticmethod
    def from_markdown_code_block(response: str) -> str:
        if "```" not in response:
            return response
        _, response, *_ = re.split("```", response)
        response = response.strip()
        if response.startswith('json'):
            response = response[4:]
        response = response.strip()

        return response
