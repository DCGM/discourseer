import unittest
import os
import shutil

from run_discourseer import Discourseer


class TestTopicExtractor(unittest.TestCase):
    dir = os.path.join(os.path.dirname(__file__), 'test_topic_extractor')

    def test_default_run(self):
        output_dir = os.path.join(self.dir, 'outputs')
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

        Discourseer(
            texts_dir=os.path.join(self.dir, 'texts-vlach'),
            ratings_dirs=[os.path.join(self.dir, 'texts-vlach-ratings-MofN')],
            output_dir=output_dir,
            topic_definitions=os.path.join(self.dir, 'topic_definitions.json'),
            prompt_definition=os.path.join(self.dir, 'prompt_definition.json')
        )()

        # test existing output dir and files
        assert os.path.exists(output_dir)

        model_ratings = os.path.join(output_dir, 'model_ratings.csv')
        assert os.path.exists(model_ratings)
        with open(model_ratings, 'r', encoding='utf-8') as f:
            assert len(f.readlines()) >= 12

        conversation_log = os.path.join(output_dir, 'conversation_log.json')
        assert os.path.exists(conversation_log)
        with open(conversation_log, 'r', encoding='utf-8') as f:
            assert len(f.readlines()) >= 50

        irr_results = os.path.join(output_dir, 'irr_results.json')
        assert os.path.exists(irr_results)
        with open(irr_results, 'r', encoding='utf-8') as f:
            assert len(f.readlines()) >= 17
            # assert no null values
            assert 'null' not in f.read().lower()
