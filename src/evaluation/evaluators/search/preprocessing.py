"""Preprocess the data for further metrics calculation."""

from typing import Dict, Tuple, List


def _preprocess_data(
    search_results: List[Dict],
    ground_truth: List[Dict],
    k: int = None,
) -> Tuple[List, List]:
    """
    Preprocess the data for the downstream metric calculation.

    The following steps are included:
    * Convert results and ground truth into a list of tuples of the following format: (filename, page number)
    * Normalize all the urls
    * Select top K items (if K is provided)


    Args:
        data (Dict): data, containing `sources` and `answer` keys for evaluation
        k (int, optional): threshold for the top K documents. Defaults to None.

    Returns:
        Tuple[List, List]: preprocessed ground truth and search results
    """
    ground_truth = [(gt["filename"].lower(), str(gt["page_number"])) for gt in ground_truth]

    # Select top K results
    if k is None:
        min_k = len(search_results)
    else:
        min_k = min(k, len(search_results))
    top_k_search_results = search_results[:min_k]

    # Extract URLs from retrieved documents, lowercase page numbers and urls
    top_k_search_results = [
        (sr["filename"].lower(), str(sr["page_number"])) for sr in top_k_search_results
    ]

    return ground_truth, top_k_search_results
