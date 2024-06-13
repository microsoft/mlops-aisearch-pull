"""Implement Evaluation Target for Azure AI Search."""

from typing import Dict, List

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import (
    QueryType,
    QueryCaptionType,
    QueryAnswerType,
    VectorizableTextQuery,
)
from src.evaluation.targets.evaluation_target import EvaluationTarget


class SearchEvaluationTarget(EvaluationTarget):
    """Implementation of `EvaluationTarget` class for Search."""

    search_client: SearchClient
    fields_to_select: List[str] = ["filename", "page_number"]

    def __init__(
        self, index_name: str, semantic_config: str, endpoint: str, key: str
    ) -> None:
        """
        Instantiate a `SearchEvaluationTarget` object.

        Args:
            index_name (str): name of the Azure AI Search index
            semantic_config (str): the name of the semantic configuration
            endpoint (str): Azure AI Search endpoint
            key (str): Azure AI Search key
        """
        credential = AzureKeyCredential(key)
        self.search_client = SearchClient(endpoint, index_name, credential=credential)
        self.semantic_config = semantic_config

    def __select_fields(self, dictionary: Dict, fields: List[str] = None) -> Dict:
        """
        Select specified fields from a dictionary.

        Args:
            dictionary (Dict): dictionary
            fields (List[str], optional): fields to select. Defaults to None.

        Returns:
            Dict: dictionary that only includes selected fields
        """
        if fields is None:
            fields = self.fields_to_select
        fields = [field for field in fields if field in dictionary.keys()]
        return {key: dictionary[key] for key in fields}

    def __call__(self, query: str, top: int = 10):
        """
        Implement search call, will be used by the evaluation framework only.

        Args:
            query (str): search query
            top (int, optional): number of top results to fetch. Defaults to 3
        """
        query_vector = VectorizableTextQuery(
            text=query, k_nearest_neighbors=1, fields="content_vector", exhaustive=True
        )

        search_results = self.search_client.search(
            search_text=query,
            vector_queries=[query_vector],
            query_type=QueryType.SEMANTIC,
            semantic_configuration_name=self.semantic_config,
            query_caption=QueryCaptionType.EXTRACTIVE,
            query_answer=QueryAnswerType.EXTRACTIVE,
            top=top,
        )
        result = list(search_results)
        result_selected_fields = [self.__select_fields(res) for res in result]
        return {"search_result": result_selected_fields}
