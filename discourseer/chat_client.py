from __future__ import annotations

import json
import os
import pydantic
from typing import Literal

import openai
from openai import OpenAI
import backoff


class Conversation(pydantic.BaseModel):
    model: str = "gpt-3.5-turbo-0125"
    max_tokens: int = 1024
    temperature: float = 0.0
    top_p: float = 0
    response_format: Literal["json", "normal"] = "json"
    messages: list[ChatMessage]


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

    def invoke(self, response_format: str | None = None, **kwargs):
        if response_format == "json":
            return self.completions_with_backoff(response_format={"type": "json_object"}, **kwargs)
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
    print(Conversation.schema_json(indent=2))


if __name__ == '__main__':
    print_conversation_schema()
