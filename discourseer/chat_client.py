import os

import openai
from openai import OpenAI
import backoff


class ChatClient:
    def __init__(self, openai_api_key: str = None):
        if openai_api_key is None:
            openai_api_key = os.environ.get("OPENAI_API_KEY", None)

        if openai_api_key is None:
            raise ValueError("OpenAI API key not provided. Please provide it as an argument `--openai-api-key` "
                             "or set the OPENAI_API_KEY environment variable.")

        self.client = OpenAI(api_key=openai_api_key)
        self.test_client()

    def invoke(self, **kwargs):
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
