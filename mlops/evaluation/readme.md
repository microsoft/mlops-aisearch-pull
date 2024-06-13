# Search Evaluation

To run the evaluation:

1. Switch to the root directory of the repo
2. Run `python -m mlops.evaluation.search_evaluation --gt_path "./data/search_evaluation_data.jsonl"  --index_name <INDEX_NAME> --semantic_config <SEMANTIC_CONFIG_NAME>`

## Notes

- The search evaluator expects the search index (and the ground truth/sources in the evaluation data) to have fields called `filename` and `page_number`.  If your index uses different fields, you might want to make changes to `/src/evaluation/evaluators/search/preprocessing.py` and `/src/evaluation/targets/search_evaluation_target.py`
