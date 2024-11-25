from __future__ import annotations

import json
import pydantic
from typing import List, Dict, Literal, Optional

single_choice_tag = "single_choice"
multiple_choice_tag = "multiple_choice"


class ExtractionPrompts(pydantic.BaseModel):
    prompts: Dict[str, ExtractionPrompt] = {}

    def __getitem__(self, item):
        return self.prompts.get(item, None)

    def __contains__(self, item):
        return item in self.prompts

    def is_multiple_choice(self, prompt: str) -> bool:
        if prompt not in self.prompts:
            return False
        return self.prompts[prompt].multiple_choice

    def select_subset(self, subset: List[str] = None) -> ExtractionPrompts:
        if not subset:
            return self
        return ExtractionPrompts(prompts={key: value for key, value in self.prompts.items() if key in subset})

    def select_unique_names_and_question_ids(self) -> ExtractionPrompts:
        unique_names = set()
        unique_question_ids = set()
        unique_prompts = {}

        duplicate_prompts = []

        for key, prompt in self.prompts.items():
            if prompt.name not in unique_names and prompt.question_id not in unique_question_ids:
                unique_names.add(prompt.name)
                unique_question_ids.add(prompt.question_id)
                unique_prompts[key] = prompt
            else:
                duplicate_prompts.append(key)

        if duplicate_prompts:
            print(f"Skipping prompts {', '.join(duplicate_prompts)} as it has duplicate names or questions.")
        return ExtractionPrompts(prompts=unique_prompts)

    def prompt_names(self) -> str:
        return ", ".join([prompt.name for prompt in self.prompts.values()])

    def prompt_descriptions(self) -> str:
        return " ".join([prompt.description for prompt in self.prompts.values()])

    def prompt_names_and_descriptions_colon(self) -> str:
        return ". ".join([f'{prompt.name}: {prompt.description}' for prompt in self.prompts.values()])

    def prompt_names_and_descriptions_parentheses(self) -> str:
        return ". ".join([f'{prompt.name} ({prompt.description})' for prompt in self.prompts.values()])

    def single_choice_prompts(self) -> str:
        return ", ".join([prompt.name for prompt in self.prompts.values() if not prompt.multiple_choice])

    def multiple_choice_prompts(self) -> str:
        return ", ".join([prompt.name for prompt in self.prompts.values() if prompt.multiple_choice])

    def prompt_options(self) -> str:
        return "\n".join([f'{prompt.name}: {prompt.list_options()}' for prompt in self.prompts.values()
                          if len(prompt.options) > 0])

    def prompt_options_with_examples(self) -> str:
        return "\n".join([f'{prompt.name}: {prompt.list_options_with_examples()}' for prompt in self.prompts.values()
                          if len(prompt.options) > 0])

    def prompt_options_with_examples_bulletpoints(self) -> str:
        return "\n".join([f'{prompt.name}:\n - {prompt.list_options_with_examples_bulletpoints()}' for prompt in self.prompts.values()
                          if len(prompt.options) > 0])

    def whole_prompt_info(self) -> str:
        """Whole prompt info in one string. Individual prompts are separated by newline."""
        return "\n".join([f"{prompt.name}: {multiple_choice_tag if prompt.multiple_choice else single_choice_tag} "
                          f"(description: {prompt.description}) options: {prompt.list_options_with_examples()}"
                          for prompt in self.prompts.values()])

    def whole_prompt_info_bulletpoints(self) -> str:
        """Whole prompt info in one string. Individual prompts are separated by newline. Info is structured using bulletpoints on two levels."""
        return "\n".join([f"{prompt.name}: {multiple_choice_tag if prompt.multiple_choice else single_choice_tag} "
                          f"(description: {prompt.description})options:\n - {prompt.list_options_with_examples_bulletpoints()}"
                          for prompt in self.prompts.values()])

    def prompts_json(self) -> str:
        return self.model_dump_json(indent=2)

    def response_json_schema(self) -> str:
        response_format = {}
        for prompt_key, prompt in self.prompts.items():
            if prompt.multiple_choice:
                value = List[str]
            else:
                value = str
            response_format[prompt_key] = (value, ...)
        response_format = pydantic.create_model('ResponseFormat', **response_format)
        return json.dumps(response_format.model_json_schema(), indent=2, ensure_ascii=False)

    def response_json_schema_with_options(self) -> str:
        response_format = {}
        for _, prompt in self.prompts.items():
            option_names = [option.name for option in prompt.options]

            if prompt.multiple_choice:
                value = List[Literal[tuple(option_names)]] if len(option_names) > 0 else List[str]
            else:
                value = Literal[tuple(option_names)] if len(option_names) > 0 else str
            response_format[prompt.name] = (value, ...)
        response_format = pydantic.create_model('ResponseFormat', **response_format)
        return json.dumps(response_format.model_json_schema(), indent=2, ensure_ascii=False)

    def get_format_strings(self) -> Dict[str, str]:
        return {
            "prompt_names": self.prompt_names(),
            "prompt_descriptions": self.prompt_descriptions(),
            "prompt_names_and_descriptions_colon": self.prompt_names_and_descriptions_colon(),
            "prompt_names_and_descriptions_parentheses": self.prompt_names_and_descriptions_parentheses(),
            "single_choice_prompts": self.single_choice_prompts(),
            "multiple_choice_prompts": self.multiple_choice_prompts(),
            "prompt_options": self.prompt_options(),
            "prompt_options_with_examples": self.prompt_options_with_examples(),
            "prompt_options_with_examples_bulletpoints": self.prompt_options_with_examples_bulletpoints(),
            "whole_prompt_info": self.whole_prompt_info(),
            "whole_prompt_info_bulletpoints": self.whole_prompt_info_bulletpoints(),
            "prompt_json": self.prompts_json(),
            "response_json_schema": self.response_json_schema(),
            "response_json_schema_with_options": self.response_json_schema_with_options(),
            "custom_format_string": self.custom_format_string(),
            # add your own format strings here with a reference to the corresponding function
        }

    def custom_format_string(self) -> str:
        # define your custom format string here with the same name
        return ". ".join([f'{prompt.name} ({prompt.description})' for prompt in self.prompts.values()])


class ExtractionPrompt(pydantic.BaseModel):
    name: str
    question_id: str
    description: str
    multiple_choice: bool = False
    options: List[ResultOption] = []

    def has_option(self, option: str) -> bool:
        return option in [option.name for option in self.options]

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


class ResultOption(pydantic.BaseModel):
    name: str
    description: str
    examples: Optional[List[str]] = []

    def to_str_bulletpoint(self) -> str:
        return self.name + " (" + self.description + ")" + (" Examples: " + "\n  - ".join(self.examples) if self.examples else "")

    def __str__(self) -> str:
        return self.name + " (" + self.description + ")" + (" Examples: " + ", ".join(self.examples) if self.examples else "")
