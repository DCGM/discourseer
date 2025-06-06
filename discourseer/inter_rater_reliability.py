from __future__ import annotations
import logging
import os
from enum import Enum

import pydantic
from typing import Optional, Dict, List

import numpy as np
import pandas as pd
from irrCAC.raw import CAC
import matplotlib.pyplot as plt
import seaborn as sns

from discourseer.rater import Rater
from discourseer.codebook import single_choice_tag
from discourseer import utils
from discourseer.utils import name_to_path

logger = logging.getLogger()


class IRRResults(pydantic.BaseModel):
    irr_result: IRRResult = None  # mean of all question IRR results
    majority_agreement: Optional[float] = None
    disagreement: Optional[float] = None
    questions: Optional[Dict[str, IRRQuestionResult]] = {}
    files: Optional[Dict[str, IRRFileResult]] = {}

    def calc_mean_through_questions(self) -> IRRResult:
        if not self.questions:
            return IRRResult.get_empty()

        self.irr_result = IRRResult.calc_mean_of_IRRResults([result.irr_result for result in self.questions.values()])
        self.irr_result.description = IRRResultDescription.mean_irr_through_questions
        return self.irr_result

    def to_dict_of_results(self) -> Dict[str, IRRResult]:
        results: Dict[str, IRRResult] = {}
        if self.irr_result is not None:
            results['irr_result'] = self.irr_result

        for question_id, irr_question_result in self.questions.items():
            if irr_question_result is not None:
                results[question_id] = irr_question_result.irr_result

        return results

    def to_dict_of_results_of_metric(self, metric: str) -> Dict[str, IRRVariants]:
        results = self.to_dict_of_results()
        return {k: getattr(v, metric) for k, v in results.items() if hasattr(v, metric)}
    
    def to_dict_of_results_of_metric_and_variant(self, metric: str, variant: str) -> Dict[str, float]:
        results = self.to_dict_of_results_of_metric(metric)
        return {k: getattr(v, variant) for k, v in results.items() if hasattr(v, variant)}

    def get_summary(self) -> Dict:
        results: Dict[str, dict] = {}
        if self.irr_result is not None:
            results['irr_result'] = self.irr_result.model_dump()
        if self.majority_agreement is not None:
            results['majority_agreement'] = self.majority_agreement
        if self.disagreement is not None:
            results['disagreement'] = self.disagreement
        return results

    def get_metric(self, metric: str) -> Dict[str, dict]:
        results = {}
        if self.irr_result is not None:
            results['irr_result'] = self.irr_result.get_metric(metric)

        results['questions'] = {question_id: irr_question_result.get_metric(metric)
                                for question_id, irr_question_result in self.questions.items() if irr_question_result is not None}

        results['files'] = {file_id: file_result.get_metric(metric)
                            for file_id, file_result in self.files.items() if file_result is not None}

        return results

    def get_metric_and_variant(self, metric: str, variant: str) -> Dict[str, dict]:
        results = self.get_metric(metric)
        if 'irr_result' in results:
            if hasattr(results['irr_result'], variant):
                results['irr_result'] = getattr(results['irr_result'], variant)
            else:
                raise KeyError(f'Variant {variant} not found in irr_result: {results["irr_result"]}')

        results['questions'] = {key: question_result.get_metric_and_variant(metric, variant)
                                for key, question_result in self.questions.items() if question_result is not None}

        results['files'] = {key: file_result.get_metric_and_variant(metric, variant)
                            for key, file_result in self.files.items() if file_result is not None}

        return results

    def select(self, files: List[str] = None,
               questions: List[str] = None, options: List[str] = None,
               metrics: List[str] = None, variants: List[str] = None,
               include_multiple_choice_questions: bool = True, include_single_choice_questions: bool = True,
               include_files: bool = True) -> Dict:
        results = {'irr_result': self.irr_result.select(files, questions, options, metrics, variants, include_multiple_choice_questions, include_single_choice_questions)}

        if 'majority_agreement' in metrics and self.majority_agreement is not None:
            results['majority_agreement'] = self.majority_agreement
        
        if 'disagreement' in metrics and self.disagreement is not None:
            results['disagreement'] = self.disagreement

        selected_questions = IRRQuestionResult.select_questions(self.questions, files, questions, options, metrics, variants, include_multiple_choice_questions, include_single_choice_questions, include_files)

        if selected_questions:
            results['questions'] = selected_questions

        selected_files: Dict[str, IRRFileResult] = {}

        for file_id, irr_file_result in self.files.items():
            if not files or file_id in files:
                selected_file = irr_file_result.select(files, questions, options, metrics, variants, include_multiple_choice_questions, include_single_choice_questions, include_files)
                if selected_file:
                    selected_files[file_id] = selected_file

        if selected_files:
            results['files'] = selected_files

        return results

    def is_empty(self) -> bool:
        return ((self.irr_result is None or self.irr_result.is_empty()) and
                self.majority_agreement is None and
                self.disagreement is None and
                not self.questions)

    def maj_agg_file_results_to_pandas(self) -> Optional[pd.DataFrame]:
        if not self.files:
            return None

        file_results = []
        for file_id, irr_file_result in self.files.items():
            if not irr_file_result:
                continue

            file_result = {'file_id': file_id}
            if irr_file_result.majority_agreement is not None:
                file_result['file_majority_agreement'] = irr_file_result.majority_agreement

            # if irr_file_result.irr_result is not None:
            #     file_result['file_disagreement'] = irr_file_result.irr_result.disagreement

            file_result.update({question_id: irr_question_result.majority_agreement
                                for question_id, irr_question_result in irr_file_result.questions.items() if irr_question_result is not None})

            file_result['file_id'] = file_id
            file_results.append(file_result)

        df = pd.DataFrame(file_results).set_index('file_id')
        df = df.sort_values(by='file_majority_agreement')

        return df

    def disagg_file_results_to_pandas(self) -> Optional[pd.DataFrame]:
        if not self.files:
            return None

        file_results = []

        # add overall result to the dataframe (gets sorted according to the file_disagreement later between all files)
        # overall_result = {
        #     'file_id': 'overall',
        #     'file_disagreement': self.disagreement}
        # for question_id, irr_question_result in self.questions.items():
        #     if irr_question_result.disagreement is not None:
        #         overall_result[question_id] = irr_question_result.disagreement
        # for question_id, irr_question_result in self.questions.items():
        #     if not irr_question_result:
        #         continue
        #     for option_id, irr_option_result in irr_question_result.options.items():
        #         if not irr_option_result:
        #             continue
        #         overall_result[f'{question_id}_{option_id}'] = irr_option_result.disagreement
        # file_results.append(overall_result)

        for file_id, irr_file_result in self.files.items():
            if not irr_file_result:
                continue

            file_result = {'file_id': file_id}
            if irr_file_result.disagreement is not None:
                file_result['file_disagreement'] = irr_file_result.disagreement

            file_result.update({question_id: irr_question_result.disagreement
                                for question_id, irr_question_result in irr_file_result.questions.items() if irr_question_result is not None})

            # add also option results with question_prefix as key
            for question_id, irr_question_result in irr_file_result.questions.items():
                if not irr_question_result or not irr_question_result.multiple_choice or not irr_question_result.options:
                    continue
                for option_id, irr_option_result in irr_question_result.options.items():
                    if not irr_option_result:
                        continue
                    file_result[f'{option_id} ({question_id})'] = irr_option_result.disagreement

            file_result['file_id'] = file_id
            file_results.append(file_result)

        df = pd.DataFrame(file_results).set_index('file_id')
        df = df.sort_values(by='file_disagreement', ascending=False)

        return df


    @classmethod
    def from_json_file(cls, file: str) -> IRRResults:
        return utils.json_file_to_pydantic(file, cls)

class IRRFileResult(pydantic.BaseModel):
    irr_result: Optional[IRRResult] = None
    majority_agreement: Optional[float]
    disagreement: Optional[float] = None
    questions: Optional[Dict[str, IRRQuestionResult]] = {}

    def calc_mean_through_questions(self) -> IRRResult:
        if not self.questions:
            return IRRResult.get_empty()

        self.irr_result = IRRResult.calc_mean_of_IRRResults([result.irr_result for result in self.questions.values()])
        self.irr_result.description = IRRResultDescription.mean_irr_through_questions_in_file
        return self.irr_result

    def get_metric(self, metric: str) -> Dict[str, IRRVariants]:
        results = {}
        if self.irr_result is not None:
            results['irr_result'] = self.irr_result.get_metric(metric)

        results['questions'] = {question_id: irr_question_result.get_metric(metric)
                                for question_id, irr_question_result in self.questions.items() if irr_question_result is not None}
        return results
    
    def get_metric_and_variant(self, metric: str, variant: str) -> Dict[str, float]:
        results = {}
        if self.irr_result is not None:
            results['irr_result'] = self.irr_result.get_metric_and_variant(metric, variant)

        results['questions'] = {question_id: question_result.get_metric_and_variant(metric, variant)
                                for question_id, question_result in self.questions.items() if question_result is not None}
        
        return results
    
    def select(self, files: List[str] = None,
            questions: List[str] = None, options: List[str] = None,
            metrics: List[str] = None, variants: List[str] = None,
            include_multiple_choice_questions: bool = True, include_single_choice_questions: bool = True,
            include_files: bool = True) -> Dict:
        results = {}

        if self.irr_result is not None:
            results['irr_result'] = self.irr_result.select(files, questions, options, metrics, variants, include_multiple_choice_questions, include_single_choice_questions)

        if 'majority_agreement' in metrics and self.majority_agreement is not None:
            results['majority_agreement'] = self.majority_agreement

        selected_questions = IRRQuestionResult.select_questions(self.questions, files, questions, options, metrics, variants, include_multiple_choice_questions, include_single_choice_questions, include_files)

        if selected_questions:
            results['questions'] = selected_questions

        return results


class IRRQuestionResult(pydantic.BaseModel):
    multiple_choice: bool
    irr_result: IRRResult = None
    majority_agreement: Optional[float] = None
    disagreement: Optional[float] = None
    options: Optional[Dict[str, IRRResult]] = {}

    def calc_mean_through_options(self) -> IRRResult:
        if not self.options:
            return IRRResult.get_empty()

        self.irr_result = IRRResult.calc_mean_of_IRRResults([result for result in self.options.values()])
        self.irr_result.description = IRRResultDescription.mean_irr_through_options
        return self.irr_result

    def get_metric(self, metric: str) -> Dict[str, IRRVariants]:
        results = {}
        if self.irr_result is not None:
            results['irr_result'] = self.irr_result.get_metric(metric)

        if not self.options:
            return results
        results['options'] = {option_id: irr_option_result.get_metric(metric)
                              for option_id, irr_option_result in self.options.items() if irr_option_result is not None}
        return results

    def get_metric_and_variant(self, metric: str, variant: str) -> Dict[str, float]:
        results = {}
        if self.irr_result is not None:
            results['irr_result'] = self.irr_result.get_metric_and_variant(metric, variant)

        if not self.options:
            return results
        results['options'] = {option_id: option_result.get_metric_and_variant(metric, variant)
                              for option_id, option_result in self.options.items() if option_result is not None}

        return results

    def select(self, files: List[str] = None,
               questions: List[str] = None, options: List[str] = None,
               metrics: List[str] = None, variants: List[str] = None,
               include_multiple_choice_questions: bool = True, include_single_choice_questions: bool = True,
               include_files: bool = True) -> Dict:
        results = {}

        if self.irr_result is not None:
            results['irr_result'] = self.irr_result.select(files, questions, options, metrics, variants, include_multiple_choice_questions, include_single_choice_questions)

        if 'majority_agreement' in metrics and self.majority_agreement is not None:
            results['majority_agreement'] = self.majority_agreement

        if not self.options:  # no options found
            return results

        if not options:  # select all options
            results['options'] = {k: v.select(files, questions, options, metrics, variants, include_multiple_choice_questions, include_single_choice_questions, include_files) for k, v in self.options.items()}
            return results

        selected_options: Dict[str, IRRResult] = {}

        for option_id, irr_result in self.options.items():
            if option_id in options:
                selected_options[option_id] = irr_result.select(files, questions, options, metrics, variants, include_multiple_choice_questions, include_single_choice_questions, include_files)

        if not selected_options:
            return results

        results['options'] = selected_options
        return results

    @staticmethod
    def select_questions(all_questions: Dict[str, IRRQuestionResult], files: List[str] = None,
            questions_to_select: List[str] = None, options: List[str] = None,
            metrics: List[str] = None, variants: List[str] = None,
            include_multiple_choice_questions: bool = True, include_single_choice_questions: bool = True,
            include_files: bool = True) -> Dict[str, IRRQuestionResult]:
        selected_questions: Dict[str, IRRQuestionResult] = {}

        for question_id, irr_question_result in all_questions.items():
            if not questions_to_select or question_id in questions_to_select:
                selected = None
                if irr_question_result.multiple_choice and include_multiple_choice_questions:
                    selected = irr_question_result.select(files, questions_to_select, options, metrics, variants, include_multiple_choice_questions, include_single_choice_questions, include_files)
                elif not irr_question_result.multiple_choice and include_single_choice_questions:
                    selected = irr_question_result.select(files, questions_to_select, options, metrics, variants, include_multiple_choice_questions, include_single_choice_questions, include_files)

                if selected:
                    selected_questions[question_id] = selected

        return selected_questions


class IRRResult(pydantic.BaseModel):
    description: Optional[IRRResultDescription] = None
    fleiss_kappa: IRRVariants
    krippendorff_alpha: IRRVariants
    gwet_ac1: IRRVariants
    majority_agreement: Optional[float] = None
    disagreement: Optional[float] = None

    def get_metric(self, metric: str) -> Optional[IRRVariants]:
        if hasattr(self, metric):
            return getattr(self, metric)
        return None

    def get_metric_and_variant(self, metric: str, variant: str) -> float:
        metric_results = self.get_metric(metric)
        if metric_results is not None:
            return metric_results.get_variant(variant)
        return None

    def select(self, files: List[str] = None,
               questions: List[str] = None, options: List[str] = None,
               metrics: List[str] = None, variants: List[str] = None,
               include_multiple_choice_questions: bool = True, include_single_choice_questions: bool = True,
               include_files: bool = True) -> Dict:
        if not metrics:
            return self.model_dump()

        results = {'description': self.description}
        for metric in metrics:
            if hasattr(self, metric) and (metric not in ['description']):
                if isinstance(getattr(self, metric), IRRVariants):
                    results[metric] = getattr(self, metric).select(files, questions, options, metrics, variants, include_multiple_choice_questions, include_single_choice_questions, include_files)
                else:
                    results[metric] = getattr(self, metric)
        return results

    def is_empty(self) -> bool:
        return (self.fleiss_kappa.is_empty() and
                self.krippendorff_alpha.is_empty() and
                self.gwet_ac1.is_empty() and
                self.majority_agreement is None and
                self.disagreement is None)

    @classmethod
    def get_empty(cls) -> IRRResult:
        return IRRResult(
            fleiss_kappa=IRRVariants(),
            krippendorff_alpha=IRRVariants(),
            gwet_ac1=IRRVariants()
        )

    @staticmethod
    def calc_mean_of_IRRResults(results: list[IRRResult]) -> IRRResult:
        if not results:
            return IRRResult.get_empty()
        return IRRResult(
            fleiss_kappa=IRRResult.calc_mean_of_IRRVariants([result.fleiss_kappa for result in results if result]),
            krippendorff_alpha=IRRResult.calc_mean_of_IRRVariants([result.krippendorff_alpha for result in results if result]),
            gwet_ac1=IRRResult.calc_mean_of_IRRVariants([result.gwet_ac1 for result in results if result]),
            majority_agreement=IRRResult.calc_mean_of_values([result.majority_agreement for result in results if result]),
            disagreement=IRRResult.calc_mean_of_values([result.disagreement for result in results if result])
        )

    @staticmethod
    def calc_mean_of_IRRVariants(results: list[IRRVariants]) -> IRRVariants:
        if not results:
            return IRRVariants()
        return IRRVariants(
            best_case=IRRResult.calc_mean_of_values([result.best_case for result in results]),
            with_model=IRRResult.calc_mean_of_values([result.with_model for result in results]),
            worst_case=IRRResult.calc_mean_of_values([result.worst_case for result in results]),
            without_model=IRRResult.calc_mean_of_values([result.without_model for result in results])
        )

    @staticmethod
    def calc_mean_of_values(values: list[float]) -> float:
        if not values:
            return None
        values = [value for value in values if value is not None]
        if not values:
            return None
        return round(sum(values) / len(values), 5)


class IRRVariants(pydantic.BaseModel):
    best_case: Optional[float] = None
    with_model: Optional[float] = None
    worst_case: Optional[float] = None
    without_model: Optional[float] = None

    def is_empty(self) -> bool:
        return (self.best_case is None and
                self.with_model is None and
                self.worst_case is None and
                self.without_model is None)
    
    def get_variant(self, variant: str) -> float:
        if hasattr(self, variant):
            return getattr(self, variant)
        return None

    def select(self, files: List[str] = None,
               questions: List[str] = None, options: List[str] = None,
               metrics: List[str] = None, variants: List[str] = None,
               include_multiple_choice_questions: bool = True, include_single_choice_questions: bool = True,
               include_files: bool = True) -> Dict:
        if not variants:
            return self.model_dump()

        results = {}
        for variant in variants:
            if hasattr(self, variant):
                results[variant] = getattr(self, variant)

        return results

class IRRResultDescription(str, Enum):
    # string enums to make it serializable to JSON
    mean_irr_through_questions = "mean IRR through questions"
    mean_irr_through_questions_in_file = "mean IRR through questions in file"
    mean_irr_through_options = "mean IRR through options"
    irr_for_single_choice_question = "IRR for single choice question"
    irr_for_this_option = "IRR for this option"


class IRR:
    DATAFRAME_NAME = 'dataframe.csv'
    TOTAL_AGREEMENT = 1.0
    WORST_CASE_VALUE = '--WORST-CASE'  # A value that should not be present in the ratings
    EMPTY_IRR_RESULTS = IRRResults(
        irr_result=IRRResult(
            fleiss_kappa=IRRVariants(),
            krippendorff_alpha=IRRVariants(),
            gwet_ac1=IRRVariants()
        ),
    )

    col_majority = 'majority'
    col_maj_agree_with_model = 'maj_agreement_with_model'
    col_disagreement = 'disagreement'
    col_model = 'model'
    col_worst_case = 'worst_case'
    col_best_case = col_majority
    index_cols = utils.result_dataframe_index_columns()
    col_non_rater_columns = [col_model, col_majority, col_maj_agree_with_model, col_worst_case, col_best_case, col_disagreement]
    col_non_input_columns = [col_model, col_majority, col_maj_agree_with_model, col_worst_case, col_best_case, col_disagreement]

    df_maj_agg_files_and_questions = None
    maj_agg_files_and_questions_file = 'majority_agreements_of_files_and_questions.csv'
    disagg_files_and_questions_file = 'disagreement_of_files_and_questions.csv'

    def __init__(self, raters: list[Rater] = None, model_rater: Rater = None, df: pd.DataFrame = None,
                 out_dir: str = 'IRR_output',
                 export_dataframes_for_options: bool = False,
                 export_majority_agreement_files_and_questions: bool = False):
        self.raters = raters
        self.model_rater = model_rater
        if model_rater:
            self.model_rater.name = self.col_model

        # self.calculate_irr_for_options = True
        self.export_dataframes_for_options = export_dataframes_for_options
        self.export_majority_agreement_files_and_questions = export_majority_agreement_files_and_questions
        self.out_dir = out_dir
        self.out_dataframe = os.path.join(self.out_dir, self.DATAFRAME_NAME)
        os.makedirs(self.out_dir, exist_ok=True)

        if self.export_dataframes_for_options:
            self.out_questions_and_options_dir = os.path.join(self.out_dir, 'question_and_option_results')
            os.makedirs(self.out_questions_and_options_dir, exist_ok=True)

        self.input_columns = []
        self.model_columns = []
        self.rater_columns = []

        self.option_results = {}

        if df is None:  # df not provided as an argument, prepare it from raters
            self.df = self.prepare_dataframe_from_raters()
            self.df = self.preprocess_dataframe(self.df)
        else:
            self.df = self.preprocess_dataframe(df)
            self.df[self.col_maj_agree_with_model] = self.df[self.col_maj_agree_with_model].astype('object').replace({'False': False, 'True': True}).astype('bool')

        if self.df is None:  # empty DataFrame after cleaning
            self.results = IRR.EMPTY_IRR_RESULTS
        else:
            self.results = self.get_inter_rater_reliability(self.df)

    def __call__(self) -> IRRResults:
        return self.results

    def prepare_dataframe_from_raters(self) -> pd.DataFrame:
        if self.model_rater is not None:
            df = self.raters_to_dataframe(self.raters + [self.model_rater])
        else:
            df = self.raters_to_dataframe(self.raters)

        df = self.reorganize_raters(df)
        return df

    def preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df_before_cleaning = df.copy()
        df = self.clean_data(df)

        if df.shape[0] == 0:
            logger.warning("Empty DataFrame after cleaning. Cannot calculate inter-rater reliability.")
            logger.debug(f"Data before cleaning (see whole dataframe in {self.out_dataframe}):\n{df_before_cleaning}")
            df_before_cleaning.to_csv(self.out_dataframe.replace('.csv', '_before_cleaning.csv'))
            return None

        return df

    def get_inter_rater_reliability(self, df: pd.DataFrame) -> IRRResults:
        self.input_columns = df.columns.difference(self.col_non_input_columns).to_list()
        self.model_columns = [self.col_model] if self.col_model in df.columns else []

        df = self.prepare_majority_agreement(df)
        df = self.prepare_disagreement(df)
        df = self.add_worst_case(df)

        logger.debug(f'Calculating inter-rater reliability for (see whole in {self.out_dataframe}):\n{df}')
        df.to_csv(self.out_dataframe)

        irr_results = IRRResults(
            majority_agreement=self.calc_majority_agreement(df),
            disagreement=self.calc_disagreement(df),
            questions=self.calculate_irr_for_each_question(df),
            files=self.calculate_irr_for_each_file(df)
        )
        irr_results.calc_mean_through_questions()
        self.df = df

        kripp_alphas_with_model = irr_results.select(metrics=['krippendorff_alpha'], variants=['with_model'], include_files=False)
        kripp_alphas_with_model_path = os.path.join(self.out_dir, f"irr_kripp_alpha_with_model.json")
        utils.dict_to_json_file(kripp_alphas_with_model, kripp_alphas_with_model_path)

        if self.col_model in df.columns and self.export_majority_agreement_files_and_questions:
            maj_agg_files = irr_results.select(metrics=['majority_agreement'], variants=['with_model'], include_multiple_choice_questions=False, include_single_choice_questions=False)
            maj_agg_files_path = os.path.join(self.out_dir, f"majority_agreements_of_files.json")
            utils.dict_to_json_file(maj_agg_files, maj_agg_files_path)

            self.export_maj_agg_files_and_questions(irr_results)
            self.export_disagg_files_and_questions(irr_results)

        return irr_results

    def calculate_irr_for_each_question(self, df: pd.DataFrame, only_maj_agreement: bool = False) -> Dict[str, IRRQuestionResult]:
        irr_question_results: Dict[str, IRRQuestionResult] = {}
        question_ids = df.index.get_level_values(self.index_cols[1]).unique().to_list()

        for question_id in question_ids:
            logger.info(f"Calculating IRR for question {question_id}")

            df_question = df.xs(question_id, level=self.index_cols[1])
            unique_options = list(df_question.index.get_level_values('option_id').unique())

            if len(unique_options) == 0:
                logger.warning(f"No ratings for question_id {question_id}. Skipping IRR calculation.")
                continue
            elif len(unique_options) == 1 and unique_options[0] == single_choice_tag:
                logger.debug(f'calculating IRR for single choice question {question_id}')
                # question is single choice, calculate IRR for the question as a whole
                if only_maj_agreement:
                    irr_question_results[question_id] = IRRQuestionResult(
                        multiple_choice=False,
                        majority_agreement=self.calc_majority_agreement(df_question),
                        disagreement=self.calc_disagreement(df_question),
                    )
                    continue
                irr_result=self.get_irr_result(df_question)
                irr_result.description = IRRResultDescription.irr_for_single_choice_question
                irr_question_results[question_id] = IRRQuestionResult(
                    multiple_choice=False,
                    irr_result=irr_result,
                    majority_agreement=irr_result.majority_agreement,
                    disagreement=irr_result.disagreement)
            else:  # multiple choice question
                irr_question_results[question_id] = self.calculate_irr_for_each_option(
                    df_question, unique_options, question_id, only_maj_agreement=only_maj_agreement)
            
        return irr_question_results

    def calculate_irr_for_each_file(self, df: pd.DataFrame, only_maj_agreement: bool = True
                                    ) -> Dict[str, IRRFileResult]:
        file_results: Dict[str, IRRFileResult] = {}
        file_ids = df.index.get_level_values(self.index_cols[0]).unique().to_list()

        for file_id in file_ids:
            df_file = df.xs(file_id, level=self.index_cols[0])

            file_result = IRRFileResult(
                    majority_agreement=self.calc_majority_agreement(df_file),
                    disagreement=self.calc_disagreement(df_file),
                    questions=self.calculate_irr_for_each_question(df_file, only_maj_agreement=only_maj_agreement)
                )
            file_result.irr_result = file_result.calc_mean_through_questions() #file_results[file_id].questions)

            file_results[file_id] = file_result

        return file_results

    def calculate_irr_for_each_option(self, df_question: pd.DataFrame, unique_options: list[str], question_id: str,
                                      only_maj_agreement: bool = False) -> IRRQuestionResult:
        option_results: Dict[str, IRRResult] = {}

        for option in unique_options:

            index_column_count = len(df_question.index.names)
            if index_column_count > 1:
                df_option = df_question.xs(option, level='option_id')
            else:
                df_option = df_question[df_question.index.get_level_values('option_id') == option]

            if df_option.shape[0] == 0:
                logger.debug(f"No ratings for option {option} in question_id {question_id}. Skipping IRR calculation.")
                continue

            logger.debug(f'calculating IRR for option "{option}" in multi choice question {question_id}')

            option_irr_result = self.get_irr_result(df_option, only_maj_agreement=only_maj_agreement)
            option_irr_result.description = IRRResultDescription.irr_for_this_option
            option_results[option] = option_irr_result

            # export dataframes for options
            if self.export_dataframes_for_options:
                df_option_output_file = os.path.join(self.out_questions_and_options_dir,
                                                     f"dataframe__{name_to_path(question_id)}__{name_to_path(option)}.csv")
                df_option.to_csv(df_option_output_file)

        irr_question_result = IRRQuestionResult(
            multiple_choice=True,
            majority_agreement=self.calc_majority_agreement(df_question),
            disagreement=self.calc_disagreement(df_question),
            options=option_results,
        )
        irr_question_result.calc_mean_through_options()

        return irr_question_result

    def get_irr_result(self, df: pd.DataFrame, only_maj_agreement: bool = False) -> IRRResult:
        maj_agreement = self.calc_majority_agreement(df)
        disagreement = self.calc_disagreement(df)
        if only_maj_agreement:
            return IRRResult(
                fleiss_kappa=IRRVariants(),
                krippendorff_alpha=IRRVariants(),
                gwet_ac1=IRRVariants(),
                majority_agreement=maj_agreement,
                disagreement=disagreement,
            )

        if self.model_rater or self.col_model in df.columns:
            cac_with_model = CAC(df.loc[:, self.input_columns + self.model_columns])
        else:
            cac_with_model = None

        cac_without_model = CAC(df.loc[:, self.input_columns])
        cac_worst_case = CAC(df.loc[:, self.input_columns + [self.col_worst_case]])
        cac_best_case = CAC(df.loc[:, self.input_columns + [self.col_best_case]])

        fleiss_kappa = IRR.calc_fleiss_kappa(cac_without_model, cac_with_model, cac_worst_case, cac_best_case)
        kripp_alpha = IRR.calc_kripp_alpha(cac_without_model, cac_with_model, cac_worst_case, cac_best_case)
        gwet_ac1 = IRR.calc_gwet_ac1(cac_without_model, cac_with_model, cac_worst_case, cac_best_case)

        return IRRResult(
            fleiss_kappa=fleiss_kappa,
            krippendorff_alpha=kripp_alpha,
            gwet_ac1=gwet_ac1,
            majority_agreement=maj_agreement,
            disagreement=disagreement,
        )

    def prepare_majority_agreement(self, df: pd.DataFrame):
        if self.col_majority in df.columns and self.col_maj_agree_with_model in df.columns:
            return df

        if self.col_majority not in df.columns:
            df[self.col_majority] = df.loc[:, self.input_columns].mode(axis=1).iloc[:, 0]

        if len(self.model_columns) == 1:
            df[self.col_maj_agree_with_model] = df[self.col_majority] == df[self.model_columns[0]]
        elif len(self.model_columns) > 1:
            df[self.col_maj_agree_with_model] = None
            logger.warning(f"Cannot calculate majority agreement. "
                           f"More than one model columns found: {self.model_columns}")
        return df

    def calc_majority_agreement(self, df: pd.DataFrame) -> float | None:
        """
        Calculate majority agreement of a model to raters.
        """
        if self.col_majority not in df.columns or self.col_maj_agree_with_model not in df.columns:
            df = self.prepare_majority_agreement(df)

        if self.col_maj_agree_with_model not in df.columns:
            logger.info(f"Cannot calculate majority agreement. "
                        f"Column '{self.col_maj_agree_with_model}' not found in DataFrame.")
            return None

        majority_agreement = df[self.col_maj_agree_with_model].sum() / df.shape[0]
        return round(majority_agreement, 3)

    def prepare_disagreement(self, df: pd.DataFrame) -> pd.DataFrame:
        """Disagreement = (# raters who disagree with model) / (total # raters)"""
        if len(self.rater_columns) == 0:
            logger.warning(f"Cannot calculate disagreement. "
                           f"No rater columns found in DataFrame.")
            return df
        if self.col_disagreement in df.columns:
            return df

        if self.col_model in df.columns:
            df[self.col_disagreement] = df[self.rater_columns].ne(df['model'], axis=0).sum(axis=1) / len(self.rater_columns)
            df[self.col_disagreement] = df[self.col_disagreement].astype('float')
    
        return df

    def calc_disagreement(self, df: pd.DataFrame) -> float | None:
        """
        Aggregate disagreement throughout the dataset.
        Disagreement = (# raters who disagree with model) / (total # raters)
        """
        if self.col_disagreement not in df.columns:
            df = self.prepare_disagreement(df)
        if self.col_disagreement not in df.columns:
            logger.info(f"Cannot calculate disagreement. "
                        f"Column '{self.col_disagreement}' not found in DataFrame even after trying to prepare it.")
            return None

        logger.info(df)
        logger.info(f"Disagreement column:\n{df[self.col_disagreement]}")

        logger.info(df[self.col_disagreement].sum())
        logger.info(df.shape[0])

        disagreement = df[self.col_disagreement].sum() / df.shape[0]
        return round(disagreement, 3)

    def reorganize_raters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get dataFrame with sparse values (possibly lots of NaNs), shift all human rater nonNaN values to the left
        in their rows.
        """
        # df = df.copy()
        df.reset_index(inplace=True)
        df_indexes = df[self.index_cols]

        # separate model and human ratings
        df_model = df[self.col_model] if self.col_model in df.columns else None
        df_raters = df[df.columns.difference([self.col_model] + self.index_cols)].copy()

        # Add padding row to avoid columns being dropped
        df_raters.loc[len(df_raters.index)] = ['<padding>'] * len(df_raters.columns)

        # reorganize human ratings and delete NaN columns
        df_raters_new = pd.DataFrame(
            df_raters.iloc[:, ::].apply(
                lambda x: x.dropna().tolist(), axis=1).tolist(),
            columns=df_raters.columns[::]
        ).iloc[:, ::]

        # drop unused padding row and columns
        df_raters_new.drop(df_raters_new.tail(1).index, inplace=True)  # drop padding row
        df_raters_new.dropna(axis=1, how='all', inplace=True)  # drop NaN columns

        for column in df_raters_new.columns:
            df_raters_new[column] = df_raters_new[column].astype('string')

        # join model and human ratings
        df_all = pd.concat([df_indexes, df_raters_new, df_model], axis=1)

        df_all.set_index(self.index_cols, inplace=True)
        return df_all

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        self.rater_columns = df.columns.difference(self.col_non_rater_columns).to_list()
        rows_before = df.shape[0]
        df = df.replace('nan', np.nan)
        # replace 'nan' strings with NaN for calculating IRR
        # ('nan' would be treated as a separate category, np.nan should be treated as missing value)

        # if model column is present, remove rows with NaN in model column
        if self.col_model in df.columns:
            df = df[df[self.col_model].notna()]

        # remove rows where all self.rater_columns are NaN
        df = df.dropna(subset=self.rater_columns, how='all')

        removed_rows = rows_before - df.shape[0]
        logger.debug(f"Removed {removed_rows}/{rows_before} rows with NaN values.")

        return df

    def add_worst_case(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.col_worst_case in df.columns:
            return df

        df[self.col_worst_case] = IRR.WORST_CASE_VALUE

        df.reset_index(inplace=True)
        # set worst case as opposite of majority agreement
        df.loc[df['option_id'] != single_choice_tag, self.col_worst_case] = df[self.col_majority].apply(self.get_opposite_rating)
        df.set_index(self.index_cols, inplace=True)

        df[self.col_worst_case] = df[self.col_worst_case].astype('string')
        return df

    def export_maj_agg_files_and_questions(self, irr_results: IRRResults):
        df_files = irr_results.maj_agg_file_results_to_pandas()
        if df_files is None:
            return

        df_files_output_file = os.path.join(self.out_dir, self.maj_agg_files_and_questions_file)
        self.df_maj_agg_files_and_questions = df_files.copy()
        df_files.to_csv(df_files_output_file)

        worst_n = 40
        if df_files.shape[0] <= worst_n // 2:
            fig, ax = plt.subplots(1, 1) #, figsize=(10, 20))
            IRR.plot_heatmap(df_files, ax)
        else:
            df_files = df_files.head(worst_n)
            df_files_1 = df_files.iloc[:worst_n//2]
            df_files_2 = df_files.iloc[worst_n//2:]

            # plot two heatmaps in the same figure
            fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(10, 20))
            IRR.plot_heatmap(df_files_1, ax0)
            IRR.plot_heatmap(df_files_2, ax1)
            ax1.legend().remove()

        fig.suptitle(f'Majority agreement for each question in each file (worst {worst_n} files)', fontsize=13)
        fig.tight_layout(rect=[0, 0, 1, 0.99])

        # save to image
        out_file = os.path.join(self.out_dir, 'majority_agreement_heatmap.png')
        plt.savefig(out_file)
        plt.close()

    def export_disagg_files_and_questions(self, irr_results: IRRResults):
        df_files = irr_results.disagg_file_results_to_pandas()
        if df_files is None:
            return

        df_files_output_file = os.path.join(self.out_dir, self.disagg_files_and_questions_file)
        self.df_disagg_files_and_questions = df_files.copy()
        df_files.to_csv(df_files_output_file)

    def get_maj_agg_files_and_questions_summary(self) -> str:
        if self.df_maj_agg_files_and_questions is None or self.df_maj_agg_files_and_questions.empty:
            return ""

        message = '3 worst files according to majority agreement:\n'
        message += self.df_maj_agg_files_and_questions.head(3).to_string()
        message += f'\n(see whole in {self.maj_agg_files_and_questions_file})\n'
        return message

    @staticmethod
    def plot_heatmap(df: pd.DataFrame, ax: plt.Axes):
        sns.heatmap(df, annot=True, fmt=".2f", ax=ax)
        ax.set_ylabel('')

        n_chars = 15

        yticks_values = np.arange(0, df.shape[0], 1) + 0.5
        yticks_labels = [f if len(f) < n_chars else f[:n_chars] + '...'
                         for f in df.index]
        ax.set_yticks(yticks_values, labels=yticks_labels)

        xticks_values = np.arange(0, df.shape[1], 1) + 0.5
        xticks_labels = [f if len(f) < n_chars else f[:n_chars] + '...'
                         for f in df.columns]
        ax.set_xticks(xticks_values, labels=xticks_labels, rotation=90)
        ax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False)


    @staticmethod
    def get_opposite_rating(rating: str) -> str:
        # check for NA first
        if pd.isna(rating):
            return rating
        elif rating == 'True':
            return 'False'
        elif rating == 'False':
            return 'True'
        return rating

    def get_reorganized_raters(self) -> pd.DataFrame:
        return self.df.loc[:, self.input_columns]

    @staticmethod
    def calc_fleiss_kappa(cac_without_model: CAC, cac_with_model: CAC = None, cac_worst_case: CAC = None,
                          cac_best_case: CAC = None) -> IRRVariants:
        """
        Calculate Fleiss' Kappa for a list of raters.
        """
        result = IRRVariants(
            without_model=IRR.get_cac_metric(cac_without_model, 'fleiss'),
            with_model=IRR.get_cac_metric(cac_with_model, 'fleiss'),
            worst_case=IRR.get_cac_metric(cac_worst_case, 'fleiss'),
            best_case=IRR.get_cac_metric(cac_best_case, 'fleiss')
        )
        return result

    @staticmethod
    def calc_kripp_alpha(cac_without_model: CAC, cac_with_model: CAC = None, cac_worst_cast: CAC = None,
                         cac_best_case: CAC = None) -> IRRVariants:
        """
        Calculate Krippendorff's Alpha for a list of raters.
        """
        result = IRRVariants(
            without_model=IRR.get_cac_metric(cac_without_model, 'krippendorff'),
            with_model=IRR.get_cac_metric(cac_with_model, 'krippendorff'),
            worst_case=IRR.get_cac_metric(cac_worst_cast, 'krippendorff'),
            best_case=IRR.get_cac_metric(cac_best_case, 'krippendorff')
        )
        return result

    @staticmethod
    def calc_gwet_ac1(cac_without_model: CAC, cac_with_model: CAC = None, cac_worst_cast: CAC = None,
                      cac_best_case: CAC = None) -> IRRVariants:
        """
        Calculate Gwet's AC1 for a list of raters.
        """
        result = IRRVariants(
            without_model=IRR.get_cac_metric(cac_without_model, 'gwet'),
            with_model=IRR.get_cac_metric(cac_with_model, 'gwet'),
            worst_case=IRR.get_cac_metric(cac_worst_cast, 'gwet'),
            best_case=IRR.get_cac_metric(cac_best_case, 'gwet')
        )
        return result

    @staticmethod
    def get_cac_metric(cac: CAC = None, metric: str = None) -> float | None:
        if cac is None:
            logger.debug("No CAC object provided. Empty data.")
            return None

        if metric is None:
            logger.debug("No metric provided.")
            return None

        if IRR.single_row(cac.ratings) or IRR.all_rows_equal(cac.ratings):
            return IRR.TOTAL_AGREEMENT
        elif IRR.is_total_disagreement(cac):
            return IRR.get_total_disagreement_value(metric)
        else:
            with np.errstate(divide='ignore', invalid='ignore'):
                result = getattr(cac, metric)()['est']['coefficient_value']
            return result

    @staticmethod
    def single_row(df: pd.DataFrame) -> bool:
        """
        Check if there is only one row and all values are the same.
        """
        return df.shape[0] < 2

    @staticmethod
    def all_rows_equal(df: pd.DataFrame) -> bool:
        """
        Check if all rows in a DataFrame are equal.
        """
        return df.apply(lambda x: x.nunique(), axis=1).eq(1).all()

    @staticmethod
    def is_total_disagreement(cac: CAC) -> bool:
        """
        Check if there is less or equal unique values than categories in the DataFrame.
        """
        return cac.ratings.nunique().sum() <= len(cac.categories)

    @staticmethod
    def get_total_disagreement_value(metric: str) -> float:
        """
        Get the value for total disagreement.
        """
        if metric in ['fleiss', 'krippendorff']:
            return -1.0
        elif metric == 'gwet':
            return 0.0
        return -42.0

    @staticmethod
    def raters_to_dataframe(raters: list[Rater]) -> pd.DataFrame:
        """
        Convert a list of raters to a pandas DataFrame.

        :param raters: List of raters
        :return: DataFrame
        """
        raters_dict = {}
        for rater in raters:
            rater.name = IRR.get_unique_rater_name(rater.name, list(raters_dict.keys()))
            raters_dict[rater.name] = rater.to_series()

        # check if all raters have the same length
        lens = [len(rater) for rater in raters_dict.values()]
        if len(set(lens)) != 1:
            for rater_name, rater in raters_dict.items():
                unique_file_lens = {rater_name: len(rater.index.get_level_values(0).unique().to_list()) for rater_name, rater in raters_dict.items()}
                if len(set(unique_file_lens.values())) != 1:
                    logger.warning(f'Raters have different numbers of unique files. Are you sure, these raters should be in one experiment?\n{unique_file_lens}')

        df = pd.DataFrame(raters_dict)
        for col in df.columns:
            df[col] = df[col].astype('string')
        return df

    @staticmethod
    def get_unique_rater_name(name: str, names: list[str]) -> str:
        """
        Return a unique name based on the input name and a list of existing names.
        """
        if name not in names:
            return name

        offset = 1
        while name in names:
            name = f"{name}_{offset}"
            offset += 1
        return name
