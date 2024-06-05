import os
import unittest

from discourseer.inter_rater_reliability import IRR, IRRResults
from discourseer.visualize_IRR import visualize_results


class TestIRRVisualization(unittest.TestCase):
    dir = os.path.join(os.path.dirname(__file__))

    def test_load(self):
        file = os.path.join(self.dir, 'irr_results.json')
        results = IRRResults.from_json_file(file)
        # print(json.dumps(results.model_dump(), indent=4))
        out_file = os.path.join(self.dir, 'test_out.png')
        visualize_results(results, out_file)

        assert os.path.exists(out_file)
