"""Calculate reciprocal rank metric for search evaluation."""

from typing import Dict, List

from .evaluator import Evaluator
from src.evaluation.evaluators.search.preprocessing import _preprocess_data


class ReciprocalRankEvaluator(Evaluator):
    """
    An evaluator to calculate the reciprocal rank of the search response.

    The reciprocal rank of a response is the multiplicative inverse of the rank of the first correct answer.
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
            Dict: Result of evaluation in the following format: `{reciprocal_rank: <value>}`
        """
        # Checking if we have an error in the results
        if len(search_result) == 0:
            return {f"reciprocal_rank": 0}

        return {"reciprocal_rank": self.evaluate(search_result, ground_truth)}

    def evaluate(self, search_result: List[Dict], ground_truth: List[Dict]) -> float:
        """
        Calculate the reciprocal rank of the search response.

        The reciprocal rank of a response is the multiplicative inverse of the rank of the first correct answer.

        Args:
            search_result (List[Dict]): an array of search results
            ground_truth (List[Dict]): an array of ground truth

        Returns:
            float: Reciprocal rank
        """
        # Preprocess data
        ground_truth, top_k_search_results = _preprocess_data(
            search_result, ground_truth
        )

        # If no ground truth provided or search results are empty
        if len(ground_truth) == 0 or len(top_k_search_results) == 0:
            return 0

        # Calculating rank of the first document
        for i, sr in enumerate(top_k_search_results):
            if sr in ground_truth:
                return 1 / (i + 1)

        return 0
