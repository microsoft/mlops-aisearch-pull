""""Example script to run search evaluation using Generative SDK."""
import os
import argparse
import nest_asyncio
import pandas as pd
import numpy as np

from typing import Dict
from functools import partial

from mlflow import MlflowClient

from azure.identity import AzureCliCredential
from azure.core.credentials import AzureKeyCredential

from azure.ai.resources.client import AIClient
from azure.ai.generative.evaluate import evaluate

from azure.search.documents import SearchClient
from azure.search.documents.models import (
    QueryType,
    QueryCaptionType,
    QueryAnswerType,
    VectorizableTextQuery,
)

from metrics.found_at_k import found_at_k

nest_asyncio.apply()


# Setup environment variables
SUBSCRIPTION_ID = os.environ.get("SUBSCRIPTION_ID")
RESOURCE_GROUP = os.environ.get("RESOURCE_GROUP")
PROJECT_NAME = os.environ.get("AI_STUDIO_PROJECT_NAME")

SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_SERVICE_ENDPOINT")
SEARCH_INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX")
SEARCH_KEY = os.environ.get("AZURE_SEARCH_KEY")


# Define search function (can depend on your index/search type)
def search(search_client: SearchClient, question: str, **kwargs) -> Dict:
    """Perform search for the given question using the given search client.

    Args:
        search_client (SearchClient): search client
        question (str): search query

    Returns:
        Dict: search results
    """
    query_vector = VectorizableTextQuery(
        text=question, k_nearest_neighbors=1, fields="vector", exhaustive=True
    )

    search_results = search_client.search(
        search_text=question,
        vector_queries=[query_vector],
        select=["parent_id", "chunk_id", "chunk"],
        query_type=QueryType.SEMANTIC,
        semantic_configuration_name="my-semantic-config",
        query_caption=QueryCaptionType.EXTRACTIVE,
        query_answer=QueryAnswerType.EXTRACTIVE,
        top=1,
    )

    result = list(search_results)
    return {
        "answer": result,
        "context": "",
    }


def log_metrics(tracking_uri: str, eval_id: str, output_path: str):
    """Log aggregated metrics at the run level into the AI Studio.

    Args:
        tracking_uri (str): MLFlow tracking uri
        eval_id (str): evaluation run id
        output_path (str): file path, containing the path to the evaluation result
    """
    # Display metrics as a data frame
    eval_df = pd.read_json(os.path.join(output_path, "eval_results.jsonl"), lines=True)

    agg_functions = {
        "found_at_3": np.mean,
    }

    # Retrieves MLFlow Client
    mlflow_client = MlflowClient(tracking_uri=tracking_uri)

    #   Logs aggregated metrics
    for metric, agg_func in agg_functions.items():
        agg_metric = agg_func(eval_df[metric].values)
        mlflow_client.log_metric(eval_id, metric, agg_metric)


def run_evaluation(
    ai_client: AIClient,
    search_client: SearchClient,
    eval_name: str,
    data_path: str,
    output_path: str = "./",
):
    """Run search evaluation.

    Args:
        ai_client (AIClient): AI Studio client
        search_client (SearchClient): AI Search client
        eval_name (str): Name of the evaluation run
        data_path (str): Path to the data
        output_path (str, optional): Path to save the result to. Defaults to "./".

    Returns:
        EvaluationResult: evaluation result
    """
    # Instantiate required parameters
    target = partial(search, search_client=search_client)

    # Run evaluation
    result = evaluate(
        evaluation_name=eval_name,
        target=target,  # The target can also be a Prompt Flow
        data=data_path,
        task_type="qa",
        data_mapping={"ground_truth": "truth"},
        metrics_list=[found_at_k],
        tracking_uri=ai_client.tracking_uri,
        output_path=output_path,
    )

    print(f"Metric summary:\n{result.metrics_summary}")
    print(f"Studio url: {result.studio_url}")
    return result


def main(eval_name: str, data_path: str, output_path: str = "./"):
    """Run evaluation and log results into the AI Studio.

    Args:
        eval_name (str): Name of the evaluation run
        data_path (str): Path to the data
        output_path (str, optional): Path to save the result to. Defaults to "./".
    """
    # Create credential
    credential = AzureKeyCredential(SEARCH_KEY)

    # Create Azure AI Search client
    search_client = SearchClient(
        SEARCH_ENDPOINT, SEARCH_INDEX_NAME, credential=credential
    )

    # Create Azure AI Studio client
    ai_client = AIClient(
        subscription_id=SUBSCRIPTION_ID,
        resource_group_name=RESOURCE_GROUP,
        project_name=PROJECT_NAME,
        credential=AzureCliCredential(),
    )

    # Set default Azure Open AI connection
    ai_client.get_default_aoai_connection().set_current_environment()

    # Run evaluation
    result = run_evaluation(ai_client, search_client, eval_name, data_path, output_path)

    # Log metrics
    evaluation_run_id = result._evaluation_id
    log_metrics(ai_client.tracking_uri, evaluation_run_id, output_path)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "eval_name", help="Name of your eval to display in AI Studio", type=str
    )
    parser.add_argument("data_path", help="Path to the data", type=str)
    parser.add_argument("output_path", help="Path to save the output to", type=str)
    args = parser.parse_args()

    main(args.eval_name, args.data_path, args.output_path)
