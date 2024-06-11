import os
import sys
import csv
from typing import List, Dict, Any, Tuple, Union
import pydantic
import re
import argparse

from discourseer.rater import Rater, Rating


class Question(pydantic.BaseModel):
    name: str
    single_choice: bool
    options: Union[List[str], Dict[int, str]] = []

    def get_option(self, index: int) -> str:
        if isinstance(self.options, dict):
            return self.options[index]
        else:
            return self.options[index]

def parse_dir(input_path: str, output_path: str):
    os.makedirs(output_path, exist_ok=True)

    for file in os.listdir(input_path):
        if not file.endswith('.csv'):
            continue
        file_path = os.path.join(input_path, file)

        # load csv file
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            data = list(reader)
        print(f'Loaded {len(data)} rows from {file_path}')
        rater = parse_spreadsheet(data)
        rater.name = file

        out_file = file if file.endswith('.csv') else f'{file}.csv'
        rater.save_to_csv(os.path.join(output_path, out_file))

def parse_spreadsheet(data) -> Rater:
    question_names_and_indexes = [(d, i) for i, d in enumerate(data[0]) if d != '']
    questions = parse_question_headers(data, question_names_and_indexes)
    print(f'Parsed {len(questions)} questions from headers: {[q.name for q in questions]}')
    ratings = parse_ratings(data, questions)
    print(f'Parsed {len(ratings)} ratings with {sum([len(r.rating_results) for r in ratings])} answers')
    return Rater(ratings=ratings)

def parse_question_headers(data, question_names_and_indexes) -> List[Question]:
    questions: List[Question] = []
    for i, (name, index) in enumerate(question_names_and_indexes):
        last_question = i == len(question_names_and_indexes) - 1
        if last_question:
            next_question_index = len(data[1])
        else:
            next_question_index = question_names_and_indexes[i+1][1]

        if next_question_index == index+1:
            # single choice question
            question = Question(name=name, single_choice=True, options=parse_single_choice_options([data[1][index]]))
        else:
            # multiple choice question
            options = [strip_stuff(o) for o in data[1][index:next_question_index]]
            question = Question(name=name, single_choice=False, 
                                options=options)
        questions.append(question)

    return questions

def strip_stuff(data: str) -> str:
    return data.strip().strip(';,.:)').strip()

def parse_single_choice_options(data: str) -> List[str]:
    if isinstance(data, list) and len(data) == 1:
        data = data[0]

    print(f'data: {data}')

    pattern = r"(\d+[\)\.\s]?)\s+"
    matches = [(m.start(0), m.end(1)) for m in re.finditer(pattern, data)]

    options_dict: Dict[int, str] = {}
    for i, match in enumerate(matches[:-1]):
        index = data[match[0]:match[1]]
        print(f'index: {index}')
        start = match[1]
        end = matches[i+1][0]
        option = data[start:end]
        options_dict[int(strip_stuff(index))] = strip_stuff(option)

    # add last option
    options_dict[int(strip_stuff(data[matches[-1][0]:matches[-1][1]]))] = strip_stuff(data[matches[-1][1]:])

    print(f'options_dict: {options_dict}')
    return options_dict

def parse_ratings(data, questions: List[Question]) -> List[Rating]:
    answer_lines = data[2:]
    ratings: List[Rating] = []

    for row in answer_lines:
        print(f'row: {row}')
        # every row should have: name of file, answers to individual questions (single or multiple columns according to question type)
        file = row[0].strip()
        if file == '':
            continue

        row_index = 1
        for question in questions:
            print('')
            print(f'row_index: {row_index}')
            print(f'question: {question.model_dump()}')
            if question.single_choice:
                print(f'row[{row_index}]: {row[row_index]}')
                answer = get_single_choice_answer(row[row_index], question)
                print(f'answer: {answer}')
                rating = Rating(file=file, question_id=question.name, rating_results=answer)
            else:
                print(f'row[{row_index}:]: {row[row_index:]}')
                answers = get_multi_choice_answers(row[row_index:], question)
                rating = Rating(file=file, question_id=question.name, rating_results=answers)

            print(f'rating: {rating.model_dump()}')
            row_index += len(question.options) if not question.single_choice else 1
            print(f'Adding {len(question.options)} to row_index ({question.model_dump()})')
            ratings.append(rating)

    return ratings

def clean_single_choice_answer(answer: str) -> str:
    answer = answer.strip().strip(';,.').strip()
    match_result = re.match(r'(\d+)', answer)
    if match_result:
        answer = match_result.group(1)
    return answer

def get_single_choice_answer(answer: str, question: Question) -> str:
    answer = clean_single_choice_answer(answer)

    if not answer:
        return []

    try:
        return [question.get_option(int(answer))]
    except KeyError:
        return []

def get_multi_choice_answers(row: List[str], question: Question) -> List[str]:
    binary_answers = row[:len(question.options)]
    answers = []

    for i, answer in enumerate(binary_answers):
        answer = clean_single_choice_answer(answer)
        if answer in ['ano', 'yes', '1', '2', '3', '4']:
            answers.append(question.options[i])

    return answers

def parse_args():
    parser = argparse.ArgumentParser(description='Parse Google Spreadsheet to ratings')
    parser.add_argument('input_path', help='Path to directory with csv files')
    parser.add_argument('output_path', help='Path to directory where to save parsed csv files')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    parse_dir(args.input_path, args.output_path)
    # example: parse_dir('experiments/gaza/coder_results_original/', 'experiments/gaza/coder_results_ratings/')
    print('Done')

"""Example input document:
,Zpravodajské hodnoty,,,,,Hlavní téma článku,Mediální rámce,,,,,,Mluvčí,,,,,,,,,,,
,Negativita negativity,Blízkost proximity,Elitní osoby prominence,Personalizace personalization,Dopad impact,"1) Vnitřní politické dění; 2) Mezinárodní politické reakce
3) Vojenské operace Izraele 4) Teroristické operace
5)  Dílčí konflikty a střety
6) Dopad na civilisty a humanitární krize
7) Humanitární pomoc 8) Globální reakce veřejnosti
9) Jiné",Rámec konfliktu,Rámec budování míru,Humanitární rámec,Historicko-kulturní rámec,Geopolitický rámec,Lokální rámec,Političtí představitelé Izraele,Političtí představitelé Palestiny,Politici z blízkovýcho>
2023-10-07T00-00-00_2023WN280011.txt,1,0,0,1,1,5,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0
2023-10-08T21-44-00_2023WN281071.txt,1,0,1,0,1,1,1,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,1 (intermediální agenda)
"""