from __future__ import annotations
import os
import logging
import pydantic
from typing import List

import pandas as pd

from discourseer.extraction_topics import ExtractionTopics, single_choice_tag

logger = logging.getLogger()


class Rating(pydantic.BaseModel):
    file: str
    topic_key: str
    topic_name: str
    rating_results: list[str]

    model_config = pydantic.ConfigDict(coerce_numbers_to_str=True)  # allow numbers to be stored as strings

    @classmethod
    def from_csv_line(cls, line: str):
        values_from_csv = line.strip().split(sep=',')
        values_from_csv = [v.strip() for v in values_from_csv]

        if len(values_from_csv) > 3:
            file, topic_key, topic_name, *rating_results = values_from_csv
            return cls(file=file, topic_key=topic_key, topic_name=topic_name, rating_results=rating_results)
        elif len(values_from_csv) == 3:
            file, topic_key, *rating_results = values_from_csv
            return cls(file=file, topic_key=topic_key, topic_name=topic_key, rating_results=rating_results)
        else:
            return None


class Rater:
    UNKNOWN_TOPIC = "<unknown_topic>"
    UNKNOWN_OPTION = "<unknown_option>"
    MOST_LIKELY_OPTION = "<most_likely_option>"

    def __init__(self, ratings: List[Rating] = None, name: str = None, extraction_topics: ExtractionTopics = None):
        """Rater consists of list of ratings. (see Rating class)"""
        self.ratings = ratings if ratings else []
        self.name = name
        self.extraction_topics = extraction_topics if extraction_topics else ExtractionTopics()
        self.name_to_key = {topic.name: key for key, topic in self.extraction_topics.topics.items()}

    def add_model_response(self, file, response: dict):
        for topic_name, value in response.items():
            logging.debug(f"Adding rating: {topic_name}, {value}")

            topic_key = self.map_name_to_topic_key(topic_name)
            if isinstance(value, str):
                value = [value]

            rating = Rating(file=file, topic_key=topic_key, topic_name=topic_name, rating_results=value)
            self.ratings.append(rating)
            logger.debug(f"saved rating: {self.ratings[-1]}")

    def map_name_to_topic_key(self, name: str) -> str:
        if name in self.extraction_topics:
            return name

        key = self.name_to_key.get(name, None)

        if not key:
            logger.warning(f"Topic name {name} not found in extraction topics. Using name as key.")
            return f'{Rater.UNKNOWN_TOPIC}{name}'
        return key

    def validate_ratings(self, topic_key: str, ratings: list[str]) -> list[str]:
        extraction_topic = self.extraction_topics[topic_key]
        if extraction_topic is None:
            return [f'{Rater.UNKNOWN_TOPIC}{r}'for r in ratings]

        valid_ratings = [Rater.validate_rating_against_topic_options(extraction_topic, r) for r in ratings]
        valid_ratings = list(set(valid_ratings))  # return unique ratings only
        return valid_ratings

    def save_to_csv(self, out_file: str):
        out_path = os.path.dirname(out_file)

        if not os.path.exists(out_path):
            os.makedirs(out_path)

        out_file = out_file if out_file.endswith('.csv') else out_file + '.csv'

        with open(out_file, 'w', encoding='utf-8') as f:
            for rating in self.ratings:
                rating_results = ','.join(rating.rating_results)
                f.write(f"{rating.file},{rating.topic_key},{rating.topic_name},{rating_results}\n")

        logger.info(f"Rater {self.name} saved to {out_file}")

    def to_series(self) -> pd.Series:
        ratings_dict = {}
        for rating in self.ratings:
            extraction_topic = self.extraction_topics[rating.topic_key]
            if extraction_topic is not None and extraction_topic.multiple_choice:
                for option in extraction_topic.options:
                    ratings_dict[(rating.file, rating.topic_key, option.name)] = option.name in rating.rating_results
            else:
                ratings_dict[(rating.file, rating.topic_key, single_choice_tag)] = rating.rating_results[0]
        series = pd.Series(ratings_dict,
                           index=pd.MultiIndex.from_tuples(
                               ratings_dict.keys(),
                               names=['file', 'topic_key', 'rating']))
        return series

    @staticmethod
    def validate_rating_against_topic_options(extraction_topic, rating) -> str:
        if extraction_topic.has_option(rating):
            return rating

        in_ratings = [o for o in extraction_topic.options
                      if rating in o.name]
        if len(in_ratings) == 1:
            return f'{Rater.MOST_LIKELY_OPTION}{rating}'

        return f'{Rater.UNKNOWN_OPTION}{rating}'

    @classmethod
    def from_csv(cls, rater_file: str, extraction_topics: ExtractionTopics = None):
        rater = cls(ratings=[], extraction_topics=extraction_topics, name=os.path.basename(rater_file))

        with open(rater_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                rating = Rating.from_csv_line(line)

                if rating is None:
                    logger.warning(f'Can not parse rating from line "{line}" in file {rater_file}. '
                                   f'Skipping.')
                    continue

                rater.ratings.append(rating)
        return rater

    @classmethod
    def from_dir(cls, ratings_dir: str = None, extraction_topics: ExtractionTopics = None) -> list[Rater]:
        if not ratings_dir or not os.path.isdir(ratings_dir):
            return []

        files = os.listdir(ratings_dir)
        raters = []

        for file in files:
            if os.path.isfile(os.path.join(ratings_dir, file)) and file.endswith('.csv'):
                raters.append(cls.from_csv(os.path.join(ratings_dir, file), extraction_topics=extraction_topics))

        return raters

    @classmethod
    def from_dirs(cls, ratings_dirs: list[str] = None, extraction_topics: ExtractionTopics = None) -> list[Rater]:
        if not ratings_dirs:
            return []

        raters = []
        for ratings_dir in ratings_dirs:
            raters += cls.from_dir(ratings_dir, extraction_topics=extraction_topics)
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
        for (file, topic_key, rating), value in series.items():
            if rating == 'single_choice':
                ratings.append(Rating(file=file, topic_key=topic_key, topic_name=topic_key, rating_results=[value]))
            elif Rater.str_to_bool(value):
                if ratings[-1].topic_key == topic_key:
                    ratings[-1].rating_results.append(rating)
                else:
                    ratings.append(
                        Rating(file=file, topic_key=topic_key, topic_name=topic_key, rating_results=[rating]))
        return cls(ratings=ratings, name=name if name else str(series.name))

    @staticmethod
    def str_to_bool(s: str | bool) -> bool:
        if isinstance(s, bool):
            return s
        return s.lower() in ['true', '1']
