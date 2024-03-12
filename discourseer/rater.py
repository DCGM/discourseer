from __future__ import annotations
import os
import logging
import pydantic

import pandas as pd

from discourseer.extraction_topics import ExtractionTopics

logger = logging.getLogger()


class Rating(pydantic.BaseModel):
    file: str
    topic_key: str
    rating_results: list[str]

    model_config = pydantic.ConfigDict(coerce_numbers_to_str=True)


class Rater:
    def __init__(self, ratings: list = None, name: str = None, extraction_topics: ExtractionTopics = None):
        """Rater consists of list of ratings. (see Rating class)"""
        self.ratings = ratings if ratings else []
        self.name = name
        self.extraction_topics = extraction_topics if extraction_topics else ExtractionTopics()
        self.name_to_key = {topic.name: key for key, topic in self.extraction_topics.topics.items()}

    def add_rating(self, file: str, topic_key: str, rating: str | list):
        logging.debug(f"Adding rating: {file}, {topic_key}, {rating}")
        rating = rating if isinstance(rating, list) else [rating]

        self.ratings.append(Rating(file=file, topic_key=topic_key, rating_results=rating))
        logger.debug(f"saved rating: {self.ratings[-1]}")

    def add_model_response(self, file, response):
        for key, value in response.items():
            topic_key = self.map_name_to_topic_key(key)
            self.add_rating(file, topic_key, value)

    def map_name_to_topic_key(self, name: str) -> str:
        if name in self.extraction_topics:
            return name

        key = self.name_to_key.get(name, None)

        if not key:
            logger.warning(f"Topic name {name} not found in extraction topics. Using name as key.")
            return name
        return key

    def save_ratings(self, out_file: str):
        out_path = os.path.dirname(out_file)

        if not os.path.exists(out_path):
            os.makedirs(out_path)

        out_file = out_file if out_file.endswith('.csv') else out_file + '.csv'

        with open(out_file, 'w', encoding='utf-8') as f:
            for rating in self.ratings:
                rating_results = ','.join(rating.rating_results)
                f.write(f"{rating.file},{rating.topic_key},{rating_results}\n")

        logger.info(f"Results saved to {out_file}")

    def to_series(self) -> pd.Series:
        ratings_dict = {}
        for rating in self.ratings:
            # print(f'rating: {dict(rating)}')

            extraction_topic = self.extraction_topics[rating.topic_key]
            # print(f'extraction_topic: {extraction_topic}')

            if extraction_topic is not None and extraction_topic.multiple_choice:
                # extraction_topic = extraction_topics[rating.topic_key]
                for option in extraction_topic.options:
                    ratings_dict[(rating.file, rating.topic_key, option.name)] = option.name in rating.rating_results
            else:
                ratings_dict[(rating.file, rating.topic_key, 'single_choice')] = rating.rating_results[0]
                # print('added just first rating')
        # print(f'ratings_dict: {ratings_dict}')
        # convert ratings_dict to series with named index 'file', 'topic_key', 'rating'
        series = pd.Series(ratings_dict,
                           index=pd.MultiIndex.from_tuples(
                               ratings_dict.keys(),
                               names=['file', 'topic_key', 'rating']))
        # print(f'series:\n{series}')
        # print('')
        return series

    @classmethod
    def from_csv(cls, rater_file: str, extraction_topics: ExtractionTopics = None):
        ratings = []
        # print('Loading rater file:', rater_file)
        with open(rater_file, 'r', encoding='utf-8') as f:
            for line in f:
                file, topic_key, *rating_results = line.strip().split(sep=',')
                # print(f'file: {file}, topic_key: {topic_key}, rating_results: {rating_results}')
                ratings.append(Rating(file=file, topic_key=topic_key, rating_results=rating_results))
                # print(f'ratings[-1]: {ratings[-1].model_dump_json(indent=2)}')
        return cls(ratings=ratings, name=os.path.basename(rater_file), extraction_topics=extraction_topics)

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
