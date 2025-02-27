from __future__ import annotations

import os
import pydantic
from typing import Literal, List, Dict, Optional
from enum import Enum
import json
import logging

import openai
from openai import OpenAI
import backoff

from discourseer.utils import JSONParser

logger = logging.getLogger()


models_max_chars = {
    'gpt-3.5-turbo-0125': 35000
}

# o_series_models = [
#     'o3',
#     'o1'
# ]

class ResponseFormat(Enum):
    json = "json"
    normal = "normal"

class Conversation(pydantic.BaseModel):
    model: str # = "gpt-3.5-turbo-0125"
    max_tokens: Optional[int] = None # 1024
    max_completion_tokens: Optional[int] = None # 4096 for reasoning models from the o series (o3, o1, ...)
    temperature: Optional[float] = None # 0.0
    reasoning_effort: Optional[Literal["low", "medium", "high"]] = None # "medium"
    top_p: Optional[float] = None # 0
    response_format: Optional[ResponseFormat] = None #ResponseFormat.json
    messages: list[ChatMessage]

    @pydantic.field_serializer('response_format')
    def serialize_response_format(self, response_format: ResponseFormat, _info):
        if response_format is None:
            return None
        return response_format.value

    def add_messages(self, messages: List[ChatMessage], try_parse_json: bool = False):
        for message in messages:
            if try_parse_json and isinstance(message.content, str):
                content_json = JSONParser.try_parse_json(message.content)
                if content_json and isinstance(content_json, dict):
                    message.content = content_json
            self.messages.append(message)

    def get_messages_length_in_chars(self):
        return sum(len(message.content) for message in self.messages)


class ChatMessage(pydantic.BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str | dict


class ConversationLog(Conversation):
    schema_definition: List[ChatMessage]
    texts: Dict[str, List[ChatMessage]] = {}


class ChatClient:
    def __init__(self, openai_api_key: str = None):
        if openai_api_key is None:
            openai_api_key = os.environ.get("OPENAI_API_KEY", None)

        if openai_api_key is None:
            raise ValueError("OpenAI API key not provided. Please provide it as an argument `--openai-api-key` "
                             "or set the OPENAI_API_KEY environment variable.")

        self.client = OpenAI(api_key=openai_api_key)
        self.test_client()

    def invoke(self, response_format: ResponseFormat = ResponseFormat.normal, **kwargs):
        # if "model" not in kwargs:
        #     raise ValueError("Model not provided in the arguments.")

        # if self.is_o_series_model(kwargs["model"]):
        #     max_tokens = kwargs.get("max_tokens", None)
        #     if max_tokens:
        #         kwargs.pop("max_tokens")
        #         kwargs["max_completion_tokens"] = max_tokens

        #     kwargs.pop("temperature", None)
        #     kwargs.pop('top_p', None)

        #     if kwargs["model"].startswith("o1"):
        #         for message in kwargs["messages"]:
        #             if message["role"] == "system":
        #                 message["role"] = "user"
        #         kwargs.pop("reasoning_effort", None)
        # else:
        #     kwargs.pop("reasoning_effort", None)

        # print(f'response_format: {response_format}')

        kwargs = self.exclude_none_values(kwargs)

        if response_format == ResponseFormat.json:
            try:
                return self.completions_with_backoff(response_format={"type": "json_object"}, **kwargs)
            except openai.BadRequestError as e:
                if "'json_object' is not supported with this model" in str(e.message):
                    logger.warning(f"Model {kwargs['model']} does not support 'json_object' response format. "
                                   "Falling back to normal response format.")
                    return self.completions_with_backoff(**kwargs)
                raise e
        else:
            return self.completions_with_backoff(**kwargs)

    @backoff.on_exception(backoff.expo, openai.RateLimitError)
    def completions_with_backoff(self, **kwargs):
        # print(f'kwargs: \n{json.dumps(kwargs, indent=2)}')
        return self.client.chat.completions.create(**kwargs)

    def test_client(self):
        try:
            response = self.invoke(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a friendly chat bot."},
                    {"role": "user", "content": "Say Hi!"},
                ],
            )
        except openai.AuthenticationError:
            raise ValueError("OpenAI API key is invalid. Please provide correct one as an argument `--openai-api-key` "
                             "or set the OPENAI_API_KEY environment variable.")
    
    def ensure_maximal_length(self, conversation: Conversation) -> Conversation:
        conversation_len = conversation.get_messages_length_in_chars()
        logger.debug(f"Messages length in chars: {conversation_len}")
        current_max_chars = models_max_chars.get(conversation.model, 35000)
        logger.debug(f"Current maximal chars: {current_max_chars}")

        if conversation_len > current_max_chars:
            excess = conversation_len - current_max_chars
            logger.warning(f"Messages length in chars exceeds the model's max tokens, shortening the last message by {excess} chars.")
            # shorten last message to fit the model's max tokens
            conversation.messages[-1].content = conversation.messages[-1].content[:-excess]
            logger.debug(f"Shortened last message to fit the model's max tokens, new length: {conversation.get_messages_length_in_chars()}")
        
        return conversation

    # def is_o_series_model(self, model: str) -> bool:
    #     return any(model.startswith(o) for o in o_series_models)

    def exclude_none_values(self, kwargs: dict) -> dict:
        return {k: v for k, v in kwargs.items() if v is not None}


def print_conversation_schema():
    print(json.dumps(Conversation.model_json_schema(), indent=2, ensure_ascii=False))


if __name__ == '__main__':
    print_conversation_schema()
