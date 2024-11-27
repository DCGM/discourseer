import json
import pydantic
import re
import os
import logging
from enum import Enum
from typing import Dict
import time

from discourseer.extraction_prompts import ExtractionPrompts

logger = logging.getLogger()


class RatingsCopyMode(Enum):
    none = "none"
    original = "original"
    reorganized = "reorganized"


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


def prepare_output_dir(output_dir: str = None, create_new: bool = True) -> str:
    if not os.path.exists(output_dir):
        if create_new:
            os.makedirs(output_dir)
        return output_dir

    output_dir_new = os.path.normpath(output_dir) + time.strftime("_%Y%m%d-%H%M%S")
    if create_new:
        os.makedirs(output_dir_new)
    logging.debug(f"Directory {output_dir} already exists. Saving the result to {output_dir_new}")
    return output_dir_new


def load_prompts(prompts_file: str = None) -> ExtractionPrompts:
    logging.debug(f'Loading prompts from file: {prompts_file}')

    if not os.path.exists(prompts_file):
        raise FileNotFoundError(f"File {prompts_file} not found.")

    with open(prompts_file, 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    prompts = ExtractionPrompts.model_validate(prompts)

    return prompts.select_unique_names_and_question_ids()


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
