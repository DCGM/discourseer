from __future__ import annotations
import os
import logging
import pydantic
from typing import List

import pandas as pd

from discourseer.extraction_prompts import ExtractionPrompts, single_choice_tag, ExtractionPrompt

logger = logging.getLogger()


class Rating(pydantic.BaseModel):
    file: str
    prompt_key: str = None
    question_id: str
    rating_results: list[str]

    model_config = pydantic.ConfigDict(coerce_numbers_to_str=True)  # allow numbers to be stored as strings

    @classmethod
    def from_csv_line(cls, line: str, question_id_to_key: dict[str, str]):
        values_from_csv = line.strip().split(sep=',')
        values_from_csv = [v.strip() for v in values_from_csv]

        if len(values_from_csv) >= 3:
            file, question_id, *rating_results = values_from_csv
            prompt_key = question_id_to_key.get(question_id, question_id)
            return cls(file=file, prompt_key=prompt_key, question_id=question_id, rating_results=rating_results)
        else:
            return None


class Rater:
    UNKNOWN_QUESTION = "<unknown_question>"
    UNKNOWN_OPTION = "<unknown_option>"
    MOST_LIKELY_OPTION = "<most_likely_option>"

    def __init__(self, ratings: List[Rating] = None, name: str = None, extraction_prompts: ExtractionPrompts = None):
        """Rater consists of list of ratings. (see Rating class)"""
        self.ratings = ratings if ratings else []
        self.name = name
        self.extraction_prompts = extraction_prompts if extraction_prompts else ExtractionPrompts()

        self.name_to_question_id = {p.name: p.question_id for p in self.extraction_prompts.prompts.values()}
        self.key_to_question_id = {key: prompt.question_id for key, prompt in self.extraction_prompts.prompts.items()}
        self.question_id_to_key = {prompt.question_id: key for key, prompt in self.extraction_prompts.prompts.items()}
        self.question_ids_to_options = {p.question_id: p.options for p in self.extraction_prompts.prompts.values()}
        self.prompt_name_to_prompt_key = {p.name: key for key, p in self.extraction_prompts.prompts.items()}

    def add_model_response(self, file, response: dict):
        """Add model response to rater. Response_id should be prompt names."""
        for response_id, value in response.items():
            logger.debug(f"Adding rating: {response_id}, {value}")
            if not value:
                logger.warning(f"None orempty value for response ID {response_id}. Skipping.")
                continue

            prompt_key = self.map_response_id_to_prompt_key(response_id)
            if not prompt_key:
                continue

            question_id = self.extraction_prompts[prompt_key].question_id

            if isinstance(value, str):
                value = [value]

            self.ratings.append(
                Rating(file=file, prompt_key=prompt_key, question_id=question_id, rating_results=value))
            logger.debug(f"saved rating: {self.ratings[-1]}")

    def map_response_id_to_prompt_key(self, response_id: str) -> str | None:
        prompt_key = self.prompt_name_to_prompt_key.get(response_id, None)
        if prompt_key:
            return prompt_key

        logger.warning(f"Response ID {response_id} not found in extraction prompts. Deleting it.")
        return None

    # def validate_ratings(self, topic_key: str, ratings: list[str]) -> list[str]:
    #     extraction_topic = self.extraction_prompts[topic_key]
    #     if extraction_topic is None:
    #         return [f'{Rater.UNKNOWN_QUESTION}{r}' for r in ratings]
    #
    #     valid_ratings = [Rater.validate_rating_against_topic_options(extraction_topic, r) for r in ratings]
    #     valid_ratings = list(set(valid_ratings))  # return unique ratings only
    #     return valid_ratings

    def save_to_csv(self, out_file: str):
        out_path = os.path.dirname(out_file)

        if not os.path.exists(out_path):
            os.makedirs(out_path)

        out_file = out_file if out_file.endswith('.csv') else out_file + '.csv'

        with open(out_file, 'w', encoding='utf-8') as f:
            for rating in self.ratings:
                rating_results = ','.join(rating.rating_results)
                f.write(f"{rating.file},{rating.question_id},{rating_results}\n")

        logger.info(f"Rater {self.name} saved to {out_file}")

    def to_series(self) -> pd.Series:
        ratings_dict = {}
        for rating in self.ratings:
            extraction_prompt = self.get_prompt_from_rating(rating)
            if extraction_prompt is not None and extraction_prompt.multiple_choice:
                for option in extraction_prompt.options:
                    ratings_dict[(rating.file, rating.question_id, option.name)] = option.name in rating.rating_results
            else:
                ratings_dict[(rating.file, rating.question_id, single_choice_tag)] = rating.rating_results[0]
        series = pd.Series(ratings_dict,
                           index=pd.MultiIndex.from_tuples(
                               ratings_dict.keys(),
                               names=['file', 'prompt_key', 'rating']))
        return series

    def get_prompt_from_rating(self, rating: Rating) -> ExtractionPrompt | None:
        if rating.prompt_key is not None and rating.prompt_key in self.extraction_prompts:
            return self.extraction_prompts[rating.prompt_key]

        prompt_key = self.question_id_to_key.get(rating.question_id, None)
        if prompt_key is not None:
            return self.extraction_prompts[prompt_key]

        logger.info(f"Rating {rating} has no prompt key or question id. Question will be seen as single choice "
                    "with an answer as the first of the list.")
        return None

    # @staticmethod
    # def validate_rating_against_prompt_options(extraction_prompt, rating) -> str:
    #     if extraction_prompt.has_option(rating):
    #         return rating
    #
    #     in_ratings = [o for o in extraction_prompt.options
    #                   if rating in o.name]
    #     if len(in_ratings) == 1:
    #         return f'{Rater.MOST_LIKELY_OPTION}{rating}'
    #
    #     return f'{Rater.UNKNOWN_OPTION}{rating}'

    @classmethod
    def from_csv(cls, rater_file: str, extraction_prompts: ExtractionPrompts = None):
        rater = cls(ratings=[], extraction_prompts=extraction_prompts, name=os.path.basename(rater_file))

        with open(rater_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                rating = Rating.from_csv_line(line, rater.question_id_to_key)

                if rating is None:
                    logger.warning(f"Can not parse rating from line {line}. Skipping.")
                    continue

                if not rating.prompt_key:
                    logger.warning(f"Question ID {rating.question_id} not found in extraction prompts. Deleting it.")
                    continue

                rater.ratings.append(rating)
        return rater

    @classmethod
    def from_dir(cls, ratings_dir: str = None, extraction_prompts: ExtractionPrompts = None) -> list[Rater]:
        if not ratings_dir or not os.path.isdir(ratings_dir):
            return []

        files = os.listdir(ratings_dir)
        raters = []

        for file in files:
            if os.path.isfile(os.path.join(ratings_dir, file)) and file.endswith('.csv'):
                raters.append(cls.from_csv(os.path.join(ratings_dir, file), extraction_prompts=extraction_prompts))

        return raters

    @classmethod
    def from_dirs(cls, ratings_dirs: list[str] = None, extraction_prompts: ExtractionPrompts = None) -> list[Rater]:
        if not ratings_dirs:
            return []

        raters = []
        for ratings_dir in ratings_dirs:
            raters += cls.from_dir(ratings_dir, extraction_prompts=extraction_prompts)
        return raters

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> List[Rater]:
        df.to_csv('test.csv')
        raters = []
        for column in df.columns:
            raters.append(cls.from_series(df[column], name=column))
        return raters

    @classmethod
    def from_series(cls, series: pd.Series, name: str = None) -> Rater:
        ratings = []
        for (file, question_id, rating), value in series.items():
            if rating == 'single_choice':
                ratings.append(Rating(file=file, question_id=question_id, rating_results=[value]))
            elif Rater.str_to_bool(value):
                if ratings[-1].question_id == question_id:
                    ratings[-1].rating_results.append(rating)
                else:
                    ratings.append(
                        Rating(file=file, question_id=question_id, rating_results=[rating]))
        return cls(ratings=ratings, name=name if name else str(series.name))

    @staticmethod
    def str_to_bool(s: str | bool) -> bool:
        if isinstance(s, bool):
            return s
        return s.lower() in ['true', '1']
