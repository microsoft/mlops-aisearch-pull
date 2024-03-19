"""A set of utility functions to prepare AI Search SDK objects."""
from azure.search.documents.indexes.models import SearchIndexer


APPLICATION_JSON_CONTENT_TYPE = "application/json"


def generate_indexer(
    file_name: str,
    values_to_assign: dict
) -> SearchIndexer:
    """
    Create SearchIndexer object based on a json file and input parameters.

    Args:
        file: The path to the json file
        values_to_assign: a dictionary with key/value pair to change in the json file

    Returns:
        SearchIndexer object
    """
    with open(file_name) as indexer_file:
        indexer_def = indexer_file.read()

    for key in values_to_assign.keys:
        indexer_def = indexer_def.replace(f"{{{key}}}", values_to_assign[key])

    indexer = SearchIndexer.deserialize(indexer_def, APPLICATION_JSON_CONTENT_TYPE)

    return indexer
