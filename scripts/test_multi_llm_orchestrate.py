import importlib.util
import pathlib
import unittest

_spec = importlib.util.spec_from_file_location(
    "mllm", pathlib.Path(__file__).with_name("multi-llm-orchestrate.py")
)
mllm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mllm)


class TestWeightedVote(unittest.TestCase):
    def test_majority_cluster_wins(self):
        responses = [
            {"node": "M1", "weight": 1.9, "text": "Oui, c'est correct."},
            {"node": "M2", "weight": 1.5, "text": "Oui c'est correct"},
            {"node": "OL1", "weight": 1.4, "text": "Non, faux."},
        ]
        out = mllm.weighted_vote(responses, threshold=0.6)
        self.assertEqual(out["winner"]["node"], "M1")
        self.assertEqual(out["agreement"], "FORT")
        self.assertGreaterEqual(out["score"], 0.6)

    def test_disagreement_is_weak(self):
        responses = [
            {"node": "M1", "weight": 1.9, "text": "réponse alpha totalement"},
            {"node": "OL1", "weight": 1.4, "text": "zzz autre chose entièrement"},
        ]
        out = mllm.weighted_vote(responses, threshold=0.6)
        self.assertEqual(out["agreement"], "FAIBLE")

    def test_empty_returns_none(self):
        out = mllm.weighted_vote([], threshold=0.6)
        self.assertIsNone(out["winner"])


if __name__ == "__main__":
    unittest.main()
