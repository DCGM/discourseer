from __future__ import annotations

import json
import pydantic
from typing import List, Dict, Literal


class ExtractionTopics(pydantic.BaseModel):
    topics: Dict[str, ExtractionTopic] = {}

    def __getitem__(self, item):
        return self.topics.get(item, None)

    def __contains__(self, item):
        return item in self.topics

    def is_multiple_choice(self, topic: str) -> bool:
        if topic not in self.topics:
            return False
        return self.topics[topic].multiple_choice

    def select_subset(self, subset: List[str] = None) -> ExtractionTopics:
        if not subset:
            return self
        return ExtractionTopics(topics={key: value for key, value in self.topics.items() if key in subset})

    def topic_keys(self) -> str:
        return ", ".join(self.topics.keys())

    def topic_names(self) -> str:
        return ", ".join([topic.name for topic in self.topics.values()])

    def topic_key_name_mapping(self) -> str:
        return ", ".join([f'{topic_key}: {topic.name}' for topic_key, topic in self.topics.items()])

    def topic_descriptions(self) -> str:
        return " ".join([topic.description for topic in self.topics.values()])

    def topic_names_and_descriptions_colon(self) -> str:
        return " ".join([f'{topic.name}: {topic.description}' for topic in self.topics.values()])

    def topic_names_and_descriptions_parentheses(self) -> str:
        return " ".join([f'{topic.name} ({topic.description})' for topic in self.topics.values()])

    def single_choice_topics(self) -> str:
        return ", ".join([topic.name for topic in self.topics.values() if not topic.multiple_choice])

    def multiple_choice_topics(self) -> str:
        return ", ".join([topic.name for topic in self.topics.values() if topic.multiple_choice])

    def topic_options(self) -> str:
        return "\n".join([f'{topic.name}: {topic.list_options_details()}' for topic in self.topics.values()
                          if len(topic.options) > 0])

    def whole_topic_info(self) -> str:
        """Whole topic info in one string. Individual topics are separated by a newline."""
        return "\n".join([f"{topic.name} {'multiple_choice' if topic.multiple_choice else 'single_choice'} "
                          f"({topic.description}) {topic.list_options_details()}"
                          for topic in self.topics.values()])

    def topics_json(self) -> str:
        return self.model_dump_json(indent=2)

    def response_json_schema(self) -> str:
        response_format = {}
        for topic_key, topic in self.topics.items():
            if topic.multiple_choice:
                value = List[str]
            else:
                value = str
            response_format[topic_key] = (value, ...)
        response_format = pydantic.create_model('ResponseFormat', **response_format)
        return json.dumps(response_format.model_json_schema(), indent=2)

    def response_json_schema_with_options(self) -> str:
        response_format = {}
        for _, topic in self.topics.items():
            option_names = [option.name for option in topic.options]

            if topic.multiple_choice:
                value = List[Literal[tuple(option_names)]] if len(option_names) > 0 else List[str]
            else:
                value = Literal[tuple(option_names)] if len(option_names) > 0 else str
            response_format[topic.name] = (value, ...)
        response_format = pydantic.create_model('ResponseFormat', **response_format)
        return json.dumps(response_format.model_json_schema(), indent=2)

    def get_format_strings(self) -> Dict[str, str]:
        return {
            "topic_keys": self.topic_keys(),
            "topic_names": self.topic_names(),
            "topic_key_name_mapping": self.topic_key_name_mapping(),
            "topic_descriptions": self.topic_descriptions(),
            "topic_names_and_descriptions_colon": self.topic_names_and_descriptions_colon(),
            "topic_names_and_descriptions_parentheses": self.topic_names_and_descriptions_parentheses(),
            "single_choice_topics": self.single_choice_topics(),
            "multiple_choice_topics": self.multiple_choice_topics(),
            "topic_options": self.topic_options(),
            "whole_topic_info": self.whole_topic_info(),
            "topics_json": self.topics_json(),
            "response_json_schema": self.response_json_schema(),
            "response_json_schema_with_options": self.response_json_schema_with_options(),
            # "text": "{text}",
        }


class ExtractionTopic(pydantic.BaseModel):
    name: str
    description: str
    multiple_choice: bool = False
    options: List[ResultOption] = []

    def has_option(self, option: str) -> bool:
        return option in [option.name for option in self.options]

    def get_description(self) -> str:
        return self.description + " " + " ".join(str(option) for option in self.options)

    def list_options(self) -> str:
        return ", ".join([option.name for option in self.options])

    def list_options_details(self) -> str:
        return ", ".join([str(option) for option in self.options])


class ResultOption(pydantic.BaseModel):
    name: str
    description: str

    def __str__(self) -> str:
        return self.name + " (" + self.description + ")"
