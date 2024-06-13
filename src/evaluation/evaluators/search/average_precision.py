"""Calculate Average Precision metric for search evaluation."""

from typing import Dict, List

from .evaluator import Evaluator
from src.evaluation.evaluators.search.preprocessing import _preprocess_data


class AveragePrecisionEvaluator(Evaluator):
    """
    An evaluator to calculate average precision (AP) score.

    AP score indicates whether all ground truth documents are ranked highly in the search results.
    """

    def __init__(self):
        """Initialize the object of the class."""
        pass

    def __call__(self, *, search_result, ground_truth):
        """
        Private method, that should be used exclusively for evaluation framework purposes.

        Args:
            search_result (List[Dict]): an array of search results
            ground_truth (List[Dict]): an array of ground truth

        Returns:
            Dict: Result of evaluation in the following format: `{average_precision: <value>}`
        """
        # Checking if we have an error in the results
        if len(search_result) == 0:
            return {f"average_precision": 0}

        return {"average_precision": self.evaluate(search_result, ground_truth)}

    def evaluate(self, search_result: List[Dict], ground_truth: List[Dict]) -> float:
        """
        Calculate average precision (AP) score.

        AP score indicates whether all ground truth documents are ranked highly in the search results.

        Args:
            search_result (List[Dict]): an array of search results
            ground_truth (List[Dict]): an array of ground truth

        Returns:
            float: Average Precision @ K
        """
        # Preprocess data
        ground_truth, search_results = _preprocess_data(search_result, ground_truth)

        # If no ground truth provided or search results are empty
        if len(ground_truth) == 0 or len(search_results) == 0:
            return 0

        # Calculate flags of correct results in the search results
        correct_results = [sr in ground_truth for sr in search_results]

        precision_sum = 0

        for i in range(0, len(search_results)):
            div = min(i, len(search_results)) + 1
            correct_results_at_i = correct_results[:div]
            precision_at_i = sum(correct_results_at_i) / div
            precision_sum += precision_at_i * correct_results[i]

        # Calculate average precision
        result = precision_sum / len(ground_truth)

        return result
