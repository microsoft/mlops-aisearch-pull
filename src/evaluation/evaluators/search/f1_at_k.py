"""Calculate F1 @ K metric for search evaluation."""

from typing import Dict, List

from src.evaluation.evaluators.search.evaluator import Evaluator
from src.evaluation.evaluators.search.precision_at_k import PrecisionAtKEvaluator
from src.evaluation.evaluators.search.recall_at_k import RecallAtKEvaluator


class F1AtKEvaluator(Evaluator):
    """An evaluator to calculate F1 score, a harmonic mean of precision and recall."""

    def __init__(self, k: int = 3):
        """Initialize the object of the class."""
        self.k = k

    def __call__(self, *, search_result, ground_truth):
        """
        Private method, that should be used exclusively for evaluation framework purposes.

        Args:
            search_result (List[Dict]): an array of search results
            ground_truth (List[Dict]): an array of ground truth

        Returns:
            Dict: Result of evaluation in the following format: `{f1_score_at_k: <value>}`
        """
        # Checking if we have an error in the results
        if len(search_result) == 0:
            return {f"f1_score_at_{self.k}": 0}

        return {f"f1_score_at_{self.k}": self.evaluate(search_result, ground_truth)}

    def evaluate(self, search_result: List[Dict], ground_truth: List[Dict]) -> float:
        """
        Calculate the F1 score of the search within the top K results.

        F1 score is a harmonic mean of precision and recall.

        Args:
            search_result (List[Dict]): an array of search results
            ground_truth (List[Dict]): an array of ground truth

        Returns:
            float: F1 score @ K
        """
        # Calculate precision
        precision_evaluator = PrecisionAtKEvaluator(k=self.k)
        precision = precision_evaluator.evaluate(search_result, ground_truth)

        # Calculate recall
        recall_evaluator = RecallAtKEvaluator(k=self.k)
        recall = recall_evaluator.evaluate(search_result, ground_truth)

        # Avoid division by zero
        div = precision + recall

        # Calculate f1 score @ K
        result = 2 * (precision * recall) / div if div > 0 else 0

        return result
