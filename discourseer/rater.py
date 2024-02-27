from __future__ import annotations
import os
import logging

import pandas as pd

logger = logging.getLogger(__name__)


class Rater:
    def __init__(self, ratings: dict = None, name: str = None):
        """Rating is a dictionary with keys (filename, response_key) and values (rating).

        Example:
        {
            "file1.txt": {
                "place": "czech-republic",
                "topics": ["immigration", "politics"],
            },
            "file2.txt": {
                "place": "ukraine",
                "topics": ["war", "politics"],
            }
        }
        """
        self.ratings = ratings if ratings else {}
        self.name = name

    def add_rating(self, file: str, question: str, rating: str | list):
        logging.debug(f"Adding rating: {file}, {question}, {rating}")
        rating = rating if isinstance(rating, list) else [rating]

        if file in self.ratings:
            self.ratings[file][question] = rating
        else:
            self.ratings[file] = {question: rating}
        logger.debug(f"saved rating: {self.ratings[file][question]}")

    def add_model_response(self, file, response):
        for key, value in response.items():
            self.add_rating(file, key, value)

    def save_ratings(self, out_file: str):
        out_path = os.path.dirname(out_file)

        if not os.path.exists(out_path):
            os.makedirs(out_path)

        out_file = out_file if out_file.endswith('.csv') else out_file + '.csv'

        with open(out_file, 'w', encoding='utf-8') as f:
            for file, ratings in self.ratings.items():
                for question, rating in ratings.items():
                    if isinstance(rating, list):
                        rating = ','.join([str(r) for r in rating])
                    else:
                        rating = str(rating)
                    # rating = ','.join(rating) if isinstance(rating, list) else str(rating)
                    f.write(f"{file},{question},{rating}\n")

    def to_series(self) -> pd.Series:
        ratings_dict = {}
        for file, ratings in self.ratings.items():
            for question, rating in ratings.items():
                if isinstance(rating, str):
                    ratings_dict[(file, question)] = rating
                elif isinstance(rating, list):
                    # TODO: implement MofN options
                    ratings_dict[(file, question)] = rating[0]
                else:
                    raise ValueError(f"Unknown rating type: {type(rating)}")

        series = pd.Series(ratings_dict)
        return series

    @classmethod
    def from_csv(cls, rater_file: str):
        ratings = {}
        with open(rater_file, 'r', encoding='utf-8') as f:
            for line in f:
                article, question, answers = line.strip().split(sep=',', maxsplit=2)
                answers = answers.strip().split(',')
                if article in ratings:
                    ratings[article][question] = answers
                else:
                    ratings[article] = {question: answers}
        return cls(ratings=ratings, name=os.path.basename(rater_file))

    @classmethod
    def from_dir(cls, ratings_dir: str = None) -> list[Rater]:
        if not ratings_dir or not os.path.isdir(ratings_dir):
            return []

        files = os.listdir(ratings_dir)
        raters = []

        for file in files:
            if os.path.isfile(os.path.join(ratings_dir, file)) and file.endswith('.csv'):
                raters.append(cls.from_csv(os.path.join(ratings_dir, file)))

        return raters

    @classmethod
    def from_dirs(cls, ratings_dirs: list[str] = None) -> list[Rater]:
        if not ratings_dirs:
            return []

        raters = []
        for ratings_dir in ratings_dirs:
            raters += cls.from_dir(ratings_dir)
        return raters
