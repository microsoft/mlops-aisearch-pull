"""
This module contains the definition of found @ K metric.
This metric calculates whether the ground truth document was found
within first K results of the search.
"""

from typing import Dict


async def found_at_k(data: Dict, k: int = 3) -> float:
    """Calculate whether the ground truth document was found within first K results of
    the search.

    Args:
        search_results (List[Dict]): list of documents retrieved by the search
        ground_truth_url (str): ground truth
        doc_url_field_name (str): name of the field in the search results dictionary,
            containing file URLs or paths
        k (int): threshold for the top K documents

    Returns:
        int: Found @ K
    """

    search_results = data.get("answer")
    ground_truth_url = data.get("truth")["url"]

    # If no ground truth provided
    if ground_truth_url is None or len(ground_truth_url) == 0:
        return 0

    # If search results are empty
    if len(search_results) == 0:
        return 0

    # Normalize ground truth URL
    ground_truth_url = ground_truth_url.lower()

    # Select top K results
    min_k = min(k, len(search_results))
    top_k_search_results = search_results[:min_k]

    # Extract URLs from retrieved documents
    docs_urls = [search_result["url"].lower() for search_result in top_k_search_results]

    # Calculate the metric
    result = float(ground_truth_url in docs_urls)

    return result
