from __future__ import annotations

import os
import pydantic
from typing import Literal
from enum import Enum
import json

import openai
from openai import OpenAI
import backoff


class ResponseFormat(Enum):
    json = "json"
    normal = "normal"


class Conversation(pydantic.BaseModel):
    model: str = "gpt-3.5-turbo-0125"
    max_tokens: int = 1024
    temperature: float = 0.0
    top_p: float = 0
    response_format: ResponseFormat = ResponseFormat.json
    messages: list[ChatMessage]

    @pydantic.field_serializer('response_format')
    def serialize_response_format(self, response_format: ResponseFormat, _info):
        return response_format.value


class ChatMessage(pydantic.BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


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
        if response_format == ResponseFormat.json:
            try:
                return self.completions_with_backoff(response_format={"type": "json_object"}, **kwargs)
            except openai.BadRequestError as e:
                if "'json_object' is not supported with this model" in str(e.message):
                    return self.completions_with_backoff(**kwargs)
                raise e
        else:
            return self.completions_with_backoff(**kwargs)

    @backoff.on_exception(backoff.expo, openai.RateLimitError)
    def completions_with_backoff(self, **kwargs):
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


def print_conversation_schema():
    print(json.dumps(Conversation.model_json_schema(), indent=2))


if __name__ == '__main__':
    print_conversation_schema()
