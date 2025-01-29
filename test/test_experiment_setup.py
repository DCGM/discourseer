import unittest
import os

from run_discourseer import Discourseer
from discourseer.codebook import Codebook
from discourseer.chat_client import Conversation
from discourseer import utils


class TestCodebooks(unittest.TestCase):
    discourseer_root = os.path.join(os.path.dirname(__file__), '..')

    def test_codebooks(self):
        codebook_dir = os.path.join(self.discourseer_root, 'codebooks')
        codebooks = os.listdir(codebook_dir)
        codebooks = [c for c in codebooks if c.endswith('.json')]

        for codebook in codebooks:
            try:
                codebook_path = os.path.join(codebook_dir, codebook)
                codebook = utils.load_codebook(codebook_path)
            except ValueError as e:
                print(f'Failed to load {codebook} with error: {e}')
                raise e

            assert isinstance(codebook, Codebook)
            assert len(codebook.questions) > 0, f'Codebook {codebook.codebook_name} has no questions'
            for question in codebook.questions:                
                assert question.id
                assert question.name
                assert question.description
                assert question.options is not None
                assert len(question.options) > 0
                assert question.options[0].id
                assert question.options[0].name

    def test_prompt_schemas(self):
        prompt_schema_dir = os.path.join(self.discourseer_root, 'prompt_schemas')
        prompt_schemas = os.listdir(prompt_schema_dir)
        prompt_schemas = [p for p in prompt_schemas if p.endswith('.json')]

        for prompt_schema in prompt_schemas:
            try:
                prompt_schema_path = os.path.join(prompt_schema_dir, prompt_schema)
                prompt_schema = Discourseer.load_prompt_schema_definition('', prompt_schema_path)
            except ValueError as e:
                print(f'Failed to load {prompt_schema} with error: {e}')
                raise e

            assert isinstance(prompt_schema, Conversation)
            self.assertTrue(hasattr(prompt_schema, 'messages'))
            assert len(prompt_schema.messages) > 0

            # test that prompt_schema has attributes of Conversation: model, max_tokens, temperature, top_p, response_format
            self.assertTrue(hasattr(prompt_schema, 'model'))
            self.assertTrue(hasattr(prompt_schema, 'max_tokens'))
            self.assertTrue(hasattr(prompt_schema, 'temperature'))
            self.assertTrue(hasattr(prompt_schema, 'top_p'))
            self.assertTrue(hasattr(prompt_schema, 'response_format'))

if __name__ == '__main__':
    unittest.main()