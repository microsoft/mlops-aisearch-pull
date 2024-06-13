"""Runs evaluation for Azure AI Search."""

import os

import argparse
from dotenv import load_dotenv
from promptflow.evals.evaluate import evaluate

from src.evaluation.evaluators.search import (
    RecallAtKEvaluator,
    PrecisionAtKEvaluator,
    F1AtKEvaluator,
    AveragePrecisionEvaluator,
    ReciprocalRankEvaluator,
)
from src.evaluation.targets.search_evaluation_target import SearchEvaluationTarget
from mlops.common.naming_utils import generate_experiment_name


def main(index_name: str, semantic_config: str, data_path: str):
    """Run evaluation for the given search index.

    Args:
        index_name (str): search index name
        semantic_config (str): semantic configuration name
        data_path (str): path to the ground truth data
    """
    experiment_name = generate_experiment_name(index_name)

    subscription_id = os.environ.get("SUBSCRIPTION_ID")
    resource_group = os.environ.get("RESOURCE_GROUP_NAME")
    project_name = os.environ.get("AI_STUDIO_PROJECT_NAME")
    azure_search_service_name = os.environ.get("ACS_SERVICE_NAME")
    azure_search_endpoint = f"https://{azure_search_service_name}.search.windows.net"
    azure_search_key = os.environ.get("ACS_API_KEY")

    target = SearchEvaluationTarget(
        index_name,
        semantic_config,
        azure_search_endpoint,
        azure_search_key,
    )

    # Define a dictionary of evaluators and their aliases
    evaluators = {
        "Recall@3": RecallAtKEvaluator(k=3),
        "Recall@5": RecallAtKEvaluator(k=5),
        "Recall@10": RecallAtKEvaluator(k=10),
        "Precision@3": PrecisionAtKEvaluator(k=3),
        "Precision@5": PrecisionAtKEvaluator(k=5),
        "Precision@10": PrecisionAtKEvaluator(k=10),
        "F1-score@3": F1AtKEvaluator(k=3),
        "F1-score@5": F1AtKEvaluator(k=5),
        "F1-score@10": F1AtKEvaluator(k=10),
        "AveragePrecision": AveragePrecisionEvaluator(),
        "ReciprocalRank": ReciprocalRankEvaluator(),
    }

    # Setup evaluator inputs (__call__ function arguments)
    evaluators_config = {
        key: {
            "search_result": "${target.search_result}",
            "ground_truth": "${data.sources}",
        }
        for key in evaluators.keys()
    }

    # Run evaluations
    results = evaluate(
        evaluation_name=experiment_name,
        data=data_path,
        target=target,
        evaluators=evaluators,
        evaluator_config=evaluators_config,
        azure_ai_project={
            "subscription_id": subscription_id,
            "resource_group_name": resource_group,
            "project_name": project_name,
        },
    )
    print(results["studio_url"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser("evaluation_parameters")
    parser.add_argument(
        "--gt_path",
        type=str,
        required=True,
        help="Path to the file containing ground truth data",
    )
    parser.add_argument(
        "--index_name",
        type=str,
        required=False,
        help="Name of the Azure AI Search index to evaluate",
    )
    parser.add_argument(
        "--semantic_config",
        type=str,
        required=True,
        help="Name of the semantic configuration to use",
    )
    args = parser.parse_args()

    load_dotenv()

    if not args.index_name:
        args.index_name = os.environ.get("BUILD_SOURCEBRANCHNAME")

    main(args.index_name, args.semantic_config, args.gt_path)
