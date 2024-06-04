import unittest


class ResponseParsing(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, True)


"""
responses seen so far:
 (what model responded) -> (what he meant, was one of the options)
 ukraine -> ukraine
 6 -> ukraine
 {'3': 1} -> 3    (range question, maybe not relevant)
 ... TODO add examples, see data/outputs
 ... TODO add option 'other' for unsuccessful paring??
"""
