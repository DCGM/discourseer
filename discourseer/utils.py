import json
import pydantic
import re
import logging

logger = logging.getLogger()


def pydantic_to_json_file(model: pydantic.BaseModel, file_path: str):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(model.model_dump(), f, ensure_ascii=False, indent=2)


class JSONParser:
    @staticmethod
    def try_parse_json(json_str) -> dict | None:
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
        _, response, *_ = re.split("```", response)
        response = response.strip()
        if response.startswith('json'):
            response = response[4:]
        response = response.strip()

        return response
