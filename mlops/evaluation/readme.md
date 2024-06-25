# Search Evaluation

To run the evaluation:

1. Switch to the root directory of the repo
2. Run `python -m mlops.evaluation.search_evaluation --gt_path "./data/search_evaluation_data.jsonl"  --index_name <INDEX_NAME> --semantic_config <SEMANTIC_CONFIG_NAME>`

## Metrics

 The following metrics are used to determine how closely the search results match the anticipated results

 - __K__: A fixed, predetermined amount of top search results to return and compare against (usually 3, 5, or 10). This metrics helps by limiting the number of results to evaluate the relevance of search results within a manageable subset.

 - __Precision @ K__: A measure of the relevance of the top `k` results in the list of returned search results. This metric calculates the proportion of top `k` items that are relevant to the query. For example, if there are `k = 10` returned search results, and 5 are deemed relevant, our precision @ 10 value would be 5/10 or 0.5.
    - Formula:
        `PRECISION @ K` = (Number of relevant items retrieved) / (Total number of items retrieved)

- __Recall @ K__: A measure of the proportion of relevant items found in the top `k` search results. This measure calculates how many of the total relevant items are captured in the top `k` search results. For example, if in a list of 100 total possible search results for a query, 20 are deemed relevant, and after a search is run to return the top `k = 10` search results 5 of the 20 total relevant results appear in the list of 10, Recall @ 10 would be 5/20 or 0.25.
    - Formula:
        `RECALL @ K` = (Number of Relevant Items Retrieved) / (Total Number of Relevant Items)

- __F1 @ K__: The harmonic mean of precision and recall, which gives both metrics equal importance.
    - Formula:
        `F1 @ K` = 2 * ((Precision @ K Value)) * ((Recall @ K Value)) / ((Precision @ K Value)) + ((Recall @ K Value))

- __Average Precision__: A measure of how well all ground truth documents are ranked in the retrieved results. This metric evaluates the precision at each position in the ranked list, averaged across all queries. For example, if there are 3 queries, each with different numbers of relevant documents, MAP will take the precision at each relevant document for all queries, average them, and then average these values across all queries.
    - Formula:

        ![AVERAGE PRECISION FORMULA](../images/Mean_Average_Precision.png "Average Precision Formula:  MAP = (1 / Q) * sum(q=1 to Q) [(1 / gt_q) * sum(k=1 to n_q) P(k) * rel(k)]")

        Where:

        - `Q` is the total number of queries
        - `gt`<sub>q</sub> is the number of ground-truth documents for the `q-th` query
        - `n`<sub>q</sub> is the number of retrived documents for the `q-th` query
        - `P(k)` is the precision at k in the list of retrieved documents
        - `rel(k)` is an indicator function equaling 1 if the item at rank k is a relevant document, 0 otherwise.

- __Reciprocal Rank__: The multiplicative inverse of the first relevant search result. For example, if, in a search that yields 10 search results, the first relevant result was the fourth result in the list, the reciprocal rank would be 1/4 or 0.25.
    - Formula:
        `RECIPROCAL_RANK`: 1 / (Order of the First Relevant Result in list)

## Notes

- The search evaluator expects the search index (and the ground truth/sources in the evaluation data) to have fields called `filename` and `page_number`.  If your index uses different fields, you might want to make changes to `/src/evaluation/evaluators/search/preprocessing.py` and `/src/evaluation/targets/search_evaluation_target.py`