Gitub workflows are in this folder.

```
python -m mlops.deployment_scripts.upload_data
python -m mlops.deployment_scripts.deploy_azure_functions
python -m mlops.deployment_scripts.run_functions
python -m mlops.deployment_scripts.build_indexer
python -m mlops.evaluation.search_evaluation --gt_path "./data/search_evaluation_data.jsonl"  --index_name <INDEX_NAME> --semantic_config <SEMANTIC_CONFIG_NAME>`
python -m mlops.deployment_scripts.cleanup_pr
```
