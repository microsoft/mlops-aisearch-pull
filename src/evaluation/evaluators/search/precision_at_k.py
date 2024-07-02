"""Calculate Precision @ K metric for search evaluation."""

from typing import Dict, List

from src.evaluation.evaluators.search.evaluator import Evaluator
from src.evaluation.evaluators.search.preprocessing import _preprocess_data


class PrecisionAtKEvaluator(Evaluator):
    """
    An evaluator to calculate how many ground truth document(s) are included in the retrieved K results.

    Precision = Number of ground truth documents retrieved / Total number of documents retrieved
    """

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
            Dict: Result of evaluation in the following format: `{precision_at_k: <value>}`
        """
        # Checking if we have an error in the results
        if len(search_result) == 0:
            return {f"precision_at_{self.k}": 0}

        return {f"precision_at_{self.k}": self.evaluate(search_result, ground_truth)}

    def evaluate(self, search_result: List[Dict], ground_truth: List[Dict]) -> float:
        """
        Calculate the precision of the search within the top K results.

        Precision @ K shows how many ground truth document(s) are included in the retrieved K results.
        Precision = Number of ground truth documents retrieved / Total number of documents retrieved

        Args:
            search_result (List[Dict]): an array of search results
            ground_truth (List[Dict]): an array of ground truth

        Returns:
            float: Precision @ K
        """
        # Preprocess data
        ground_truth, top_k_search_results = _preprocess_data(
            search_result, ground_truth, self.k
        )

        # If no ground truth provided or search results are empty
        if len(ground_truth) == 0 or len(top_k_search_results) == 0:
            return 0

        # Calculate number of correct results in the search results
        correct_results = [sr for sr in top_k_search_results if sr in ground_truth]

        # Calculate precision @ K
        result = len(correct_results) / len(top_k_search_results)

        return result
