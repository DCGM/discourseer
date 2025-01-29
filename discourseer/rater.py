from __future__ import annotations
import os
import logging
import pydantic
from typing import List

import pandas as pd

from discourseer import utils
from discourseer.codebook import Codebook, single_choice_tag, Question

logger = logging.getLogger()


class Rating(pydantic.BaseModel):
    file: str
    question_id: str
    rated_option_ids: list[str]

    model_config = pydantic.ConfigDict(coerce_numbers_to_str=True)  # allow numbers to be stored as strings

    @classmethod
    def from_csv_line(cls, line: str):#, question_id_to_key: dict[str, str]):
        values_from_csv = line.strip().split(sep=',')
        values_from_csv = [v.strip() for v in values_from_csv]

        if len(values_from_csv) >= 3:
            file, question_id, *rated_option_ids = values_from_csv
            return cls(file=file, question_id=question_id, rated_option_ids=rated_option_ids)
        else:
            return None


class Rater:

    def __init__(self, ratings: List[Rating] = None, name: str = None, codebook: Codebook = None):
        """Rater consists of list of ratings. (see Rating class)"""
        self.ratings = ratings if ratings else []
        self.name = name
        self.codebook = codebook if codebook else Codebook()

        self.not_matched_response_names = {}  # {response_name: response_value}
        self.not_matched_response_values = {}  # {question_id: response_value}

        self.question_name_to_question_id = {question.name: question.id for question in self.codebook.questions}
        assert len(self.question_name_to_question_id) == len(self.codebook.questions), \
            "Question names are not unique: " + ', '.join([p.name for p in self.codebook.questions.values()])

        self.option_name_to_option_id = {}  # {question_id: {option_name: option_key}}
        for question in self.codebook.questions:
            self.option_name_to_option_id[question.id] = {option.name: option.id for option in question.options}
            assert len(self.option_name_to_option_id[question.id]) == len(question.options), \
                f"Option names are not unique for question {question.id}: " + ', '.join([o.name for o in question.options])

    def add_model_response(self, file, response: dict):
        """Add model response to rater. Response_id should be question names."""
        for response_name, response_value in response.items():
            logger.debug(f"Adding rating: {response_name}, {response_value}")

            question_id = self.question_name_to_question_id.get(response_name, None)
            if not question_id:
                logger.warning(f"Response name {response_name} not found in question names. Skipping.")
                self.not_matched_response_names[response_name] = response_value
                continue

            if not response_value:
                logger.warning(f"None or empty response_value for response ID {response_name}. Skipping.")
                self.not_matched_response_values[question_id] = response_value
                continue

            if isinstance(response_value, str):
                response_value = [response_value]

            # match response names to response ids
            matched_response_ids = []
            for response_option_name in response_value:
                option_id = self.option_name_to_option_id[question_id].get(response_option_name, None)
                if not option_id:
                    logger.warning(f"Response option name {response_option_name} not found in question options. Skipping.")
                    self.not_matched_response_values[question_id] = response_option_name
                    continue
                matched_response_ids.append(option_id)

            if matched_response_ids:
                new_rating = Rating(file=file, question_id=question_id, rated_option_ids=matched_response_ids)
                self.ratings.append(new_rating)
                logger.debug(f"saved rating: {new_rating}")

    def save_to_csv(self, out_file: str):
        out_path = os.path.dirname(out_file)

        if not os.path.exists(out_path):
            os.makedirs(out_path)

        out_file = out_file if out_file.endswith('.csv') else out_file + '.csv'

        with open(out_file, 'w', encoding='utf-8') as f:
            for rating in self.ratings:
                rated_option_ids = ','.join(rating.rated_option_ids)
                f.write(f"{rating.file},{rating.question_id},{rated_option_ids}\n")

        logger.info(f"Rater {self.name} saved to {out_file}")

    def to_series(self) -> pd.Series:
        ratings_dict = {}
        for rating in self.ratings:
            question = self.codebook[rating.question_id]
            if question is not None and question.multiple_choice:
                for option in question.options:
                    ratings_dict[(rating.file, rating.question_id, option.id)] = option.id in rating.rated_option_ids
            else:
                ratings_dict[(rating.file, rating.question_id, single_choice_tag)] = rating.rated_option_ids[0]

        # sort ratings_dict by only file and leave question_id and rating as they are
        ratings_dict = dict(sorted(ratings_dict.items(), key=lambda x: x[0][0]))

        series = pd.Series(ratings_dict,
                           index=pd.MultiIndex.from_tuples(
                               ratings_dict.keys(),
                               names=utils.result_dataframe_index_columns()))
        series.name = self.name
        return series

    @classmethod
    def from_csv(cls, rater_file: str, codebook: Codebook = None):
        rater = cls(ratings=[], codebook=codebook, name=os.path.basename(rater_file))

        with open(rater_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                rating = Rating.from_csv_line(line) #, rater.question_id_to_key)

                if rating is None:
                    raise ValueError(f"Error parsing file {rater_file} at line: {i+1}. Content: {line}")

                rater.ratings.append(rating)
        return rater

    @classmethod
    def from_dir(cls, ratings_dir: str = None, codebook: Codebook = None) -> list[Rater]:
        if not ratings_dir or not os.path.isdir(ratings_dir):
            return []

        files = os.listdir(ratings_dir)
        raters = []

        for file in files:
            if os.path.isfile(os.path.join(ratings_dir, file)) and file.endswith('.csv'):
                raters.append(cls.from_csv(os.path.join(ratings_dir, file), codebook=codebook))

        return raters

    @classmethod
    def from_dirs(cls, ratings_dirs: list[str] = None, codebook: Codebook = None) -> list[Rater]:
        if not ratings_dirs:
            return []

        raters = []
        for ratings_dir in ratings_dirs:
            raters += cls.from_dir(ratings_dir, codebook=codebook)
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
                ratings.append(Rating(file=file, question_id=question_id, rated_option_ids=[value]))
            elif Rater.str_to_bool(value):
                if len(ratings) > 0 and ratings[-1].question_id == question_id:
                    ratings[-1].rated_option_ids.append(rating)
                else:
                    ratings.append(
                        Rating(file=file, question_id=question_id, rated_option_ids=[rating]))
        return cls(ratings=ratings, name=name if name else str(series.name))

    @staticmethod
    def str_to_bool(s: str | bool) -> bool:
        if isinstance(s, bool):
            return s
        return s.lower() in ['true', '1']
