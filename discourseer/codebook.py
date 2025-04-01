from __future__ import annotations

import logging
import json
import pydantic
from typing import List, Dict, Literal, Optional
from copy import deepcopy

logger = logging.getLogger()

single_choice_tag = "single_choice"
multiple_choice_tag = "multiple_choice"
all_questions_at_once_tag = "all_questions_at_once"


class Codebook(pydantic.BaseModel):
    codebook_name: Optional[str] = None
    codebook_version: Optional[str] = None
    questions: List[Question] = []

    def __getitem__(self, question_id: str) -> Question:
        for question in self.questions:
            if question.id == question_id:
                return question

        return None

    def __contains__(self, question_id: str) -> bool:
        for question in self.questions:
            if question.id == question_id:
                return True
        return False

    def is_empty(self) -> bool:
        return (self.codebook_name is None and
                self.codebook_version is None and 
                len(self.questions) == 0)

    def is_multiple_choice(self, question_id: str) -> bool:
        for question in self.questions:
            if question.id == question_id:
                return question.multiple_choice

        return None

    def select_subset(self, subset: List[str] = None) -> Codebook:
        # select subset of question via question ids
        if not subset:
            return self
        self.questions = [question for question in self.questions if question.id in subset]
        return self  # for optional chaining select calls

    def select_unique_names(self) -> Codebook:
        unique_names = set()
        unique_questions = []

        duplicate_question_ids = []

        for question in self.questions:
            if question.id not in unique_names:
                unique_names.add(question.id)
                unique_questions.append(question)
            else:
                duplicate_question_ids.append(question.id)

        if duplicate_question_ids:
            print(f"Skipping {len(duplicate_question_ids)} questions {', '.join(duplicate_question_ids)} as it has duplicate names.")

        self.questions = unique_questions
        return self  # for optional chaining select calls

    def split_by_individual_questions(self) -> List[Codebook]:
        codebooks = []
        for i, question in enumerate(self.questions):
            new_codebook = deepcopy(self)
            new_codebook.questions = [question]
            codebooks.append(new_codebook)

        return codebooks

    def question_names(self) -> str:
        return ", ".join([question.name for question in self.questions])

    def question_descriptions(self) -> str:
        return " ".join([question.description for question in self.questions])

    def question_names_and_descriptions_colon(self) -> str:
        return ". ".join([f'{question.name}: {question.description}' for question in self.questions])

    def question_names_and_descriptions_parentheses(self) -> str:
        return ". ".join([f'{question.name} ({question.description})' for question in self.questions])

    def single_choice_questions(self) -> str:
        return ", ".join([question.name for question in self.questions if not question.multiple_choice])

    def multiple_choice_questions(self) -> str:
        return ", ".join([question.name for question in self.questions if question.multiple_choice])

    def first_question_single_or_multi_choice(self) -> str:
        try:
            first_question = self.questions[0]
        except IndexError:
            raise ValueError(f"No questions defined in the codebook (codebook_name: {self.codebook_name}, codebook_version: {self.codebook_version}).")


        if first_question.multiple_choice:
            return "multiple choice, meaning you can select multiple options."
        else:
            return "single choice, meaning you can select only one option."

    def question_options(self) -> str:
        return "\n".join([f'{question.name}: {question.list_options()}' for question in self.questions
                          if len(question.options) > 0])

    def question_options_with_examples(self) -> str:
        return "\n".join([f'{question.name}: {question.list_options_with_examples()}' for question in self.questions
                          if len(question.options) > 0])

    def question_options_with_examples_bulletpoints(self) -> str:
        return "\n".join([f'{question.name}:\n - {question.list_options_with_examples_bulletpoints()}' for question in self.questions
                          if len(question.options) > 0])

    def whole_question_info(self) -> str:
        """Whole question info in one string. Individual questions are separated by newline."""
        return "\n".join([f"{question.name}: {multiple_choice_tag if question.multiple_choice else single_choice_tag} "
                          f"(description: {question.description}) options: {question.list_options_with_examples()}"
                          for question in self.questions])

    def whole_question_info_bulletpoints(self) -> str:
        """Whole question info in one string. Individual questions are separated by newline. Info is structured using bulletpoints on two levels."""
        return "\n".join([f"{question.name}: {multiple_choice_tag if question.multiple_choice else single_choice_tag} "
                          f"(description: {question.description})options:\n - {question.list_options_with_examples_bulletpoints()}"
                          for question in self.questions])

    def questions_json(self) -> str:
        keys_not_meant_for_chat = []  # choose what keys don't go to chat client

        questions_json = {}
        for question in self.questions:
            question_dict = question.model_dump()
            for key in keys_not_meant_for_chat:
                question_dict.pop(key, None)
            questions_json[question.id] = question_dict

        output_dict = {'questions': questions_json}
        output_str = json.dumps(output_dict, indent=2, ensure_ascii=False)
        return output_str

    def response_json_schema(self) -> str:
        response_format = {}
        for question in self.questions:
            if question.multiple_choice:
                value = List[str]
            else:
                value = str
            response_format[question.name] = (value, ...)
        response_format = pydantic.create_model('ResponseFormat', **response_format)
        return json.dumps(response_format.model_json_schema(), indent=2, ensure_ascii=False)

    def response_json_schema_with_options(self) -> str:
        response_format = {}
        for question in self.questions:
            option_names = [option.name for option in question.options]

            if question.multiple_choice:
                value = List[Literal[tuple(option_names)]] if len(option_names) > 0 else List[str]
            else:
                value = Literal[tuple(option_names)] if len(option_names) > 0 else str
            response_format[question.name] = (value, ...)
        response_format = pydantic.create_model('ResponseFormat', **response_format)
        return json.dumps(response_format.model_json_schema(), indent=2, ensure_ascii=False)

    def check_correct_usage_of_format_strings(self, message_content):
        if len(self.questions) == 0:
            raise ValueError("No questions defined in the codebook.")
        elif len(self.questions) > 1 and '{first_question_single_or_multi_choice}' in message_content:
            logger.warning(
                f"'first_question_single_or_multi_choice' format string defined in the prompt schema which should be used for experiments with individual questions. "
                f"Only the first question '{self.questions[0].name}' will be used. Out of {len(self.questions)} questions: {self.question_names()}. "
                f"If you want to prompt model with individual questions, define '\"prompt_individual_questions\":true' in the prompt schema.")

    def get_format_strings(self) -> Dict[str, str]:
        return {
            "question_names": self.question_names(),
            "question_descriptions": self.question_descriptions(),
            "question_names_and_descriptions_colon": self.question_names_and_descriptions_colon(),
            "question_names_and_descriptions_parentheses": self.question_names_and_descriptions_parentheses(),
            "single_choice_questions": self.single_choice_questions(),
            "multiple_choice_questions": self.multiple_choice_questions(),
            "first_question_single_or_multi_choice": self.first_question_single_or_multi_choice(),
            "question_options": self.question_options(),
            "question_options_with_examples": self.question_options_with_examples(),
            "question_options_with_examples_bulletpoints": self.question_options_with_examples_bulletpoints(),
            "whole_question_info": self.whole_question_info(),
            "whole_question_info_bulletpoints": self.whole_question_info_bulletpoints(),
            "questions_json": self.questions_json(),
            "response_json_schema": self.response_json_schema(),
            "response_json_schema_with_options": self.response_json_schema_with_options(),
            "custom_format_string": self.custom_format_string(),
            # add your own format strings here with a reference to the corresponding function
        }

    def custom_format_string(self) -> str:
        # define your custom format string here with the same name
        return ". ".join([f'{question.name} ({question.description})' for question in self.questions])


class Question(pydantic.BaseModel):
    id: str
    name: str
    description: str
    multiple_choice: bool = False
    options: List[Option] = []

    def has_option_id(self, option_id: str) -> bool:
        return option_id in self.options

    def has_option_name(self, option_name: str) -> bool:
        for option in self.options:
            if option.name == option_name:
                return True
        return False        

    def get_description(self) -> str:
        return self.description + " " + " ".join(str(option) for option in self.options)

    def list_option_names(self) -> str:
        return ", ".join([option.name for option in self.options])

    def list_options(self) -> str:
        return ", ".join([option.name + " (" + option.description + ")" for option in self.options])

    def list_options_with_examples(self) -> str:
        return ", ".join([str(option) for option in self.options])

    def list_options_with_examples_bulletpoints(self) -> str:
        return "\n - ".join([option.to_str_bulletpoint() for option in self.options])


class Option(pydantic.BaseModel):
    id: str
    name: str
    description: str
    examples: Optional[List[str]] = []

    def to_str_bulletpoint(self) -> str:
        return self.name + " (" + self.description + ")" + (" Examples: " + "\n  - ".join(self.examples) if self.examples else "")

    def __str__(self) -> str:
        return self.name + " (" + self.description + ")" + (" Examples: " + ", ".join(self.examples) if self.examples else "")
