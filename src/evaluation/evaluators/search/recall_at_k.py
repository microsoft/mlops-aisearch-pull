"""Calculate Recall @ K metric for search evaluation."""

from typing import Dict, List

from .evaluator import Evaluator
from src.evaluation.evaluators.search.preprocessing import _preprocess_data


class RecallAtKEvaluator(Evaluator):
    """
    An evaluator to calculate Recall @ K.

    Recall @ K shows the rate of the ground truth documents (out of all ground truth documents)
    found within first K results of the search.
    Recall = Number of ground truth documents retrieved / Total number of ground truth documents
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
            Dict: Result of evaluation in the following format: `{recall_at_k: <value>}`
        """
        # Checking if we have an error in the results
        if len(search_result) == 0:
            return {f"recall_at_{self.k}": 0}

        return {f"recall_at_{self.k}": self.evaluate(search_result, ground_truth)}

    def evaluate(self, search_result: List[Dict], ground_truth: List[Dict]) -> float:
        """
        Calculate Recall @ K.

        Recall @ K shows the rate of the ground truth documents (out of all ground truth documents)
        found within first K results of the search.
        Recall = Number of ground truth documents retrieved / Total number of ground truth documents

        Args:
            search_result (List[Dict]): an array of search results
            ground_truth (List[Dict]): an array of ground truth

        Returns:
            float: Recall @ K
        """
        # Preprocess data
        ground_truth, top_k_search_results = _preprocess_data(
            search_result, ground_truth, self.k
        )

        # If no ground truth provided or search results are empty
        if len(ground_truth) == 0 or len(top_k_search_results) == 0:
            return 0

        # Calculate intersection
        set_top_k_search_results = set(top_k_search_results)
        set_ground_truth = set(ground_truth)
        intersection = set_top_k_search_results & set_ground_truth

        # Calculate recall @ K
        result = len(intersection) / len(set_ground_truth)

        return result
