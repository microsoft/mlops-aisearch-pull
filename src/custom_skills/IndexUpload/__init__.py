import azure.functions as func
import os
import logging
import json
import jsonschema
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
import time


REQUEST_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "request_schema.json")


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Upload documents to an Azure Cognitive Search index."""
    logging.info("Python HTTP trigger function processed a request.")

    request = req.get_json()

    try:
        jsonschema.validate(request, schema=get_request_schema())
    except jsonschema.exceptions.ValidationError as e:
        return func.HttpResponse("Invalid request: {0}".format(e), status_code=400)

    errors = []
    values = []
    for value in request["values"]:
        record_id = value["recordId"]
        function_check = value["functionCheck"] if "functionCheck" in value else False
        data = value["data"]
        ids = value["identifiers"]

        search_index_name = os.environ.get("AZURE_SEARCH_INDEX_NAME")
        index_search_client = SearchClient(
            os.environ.get("AZURE_SEARCH_ENDPOINT"),
            index_name=search_index_name,
            credential=AzureKeyCredential(os.environ.get("AZURE_SEARCH_API_KEY")),
        )

        populate_index(data, index_search_client)

        if function_check:
            # Function was only called to test so we can remove
            # the data after verifying it was uploaded
            function_check_success = check_data(ids, index_search_client)
            cleanup_data(ids, index_search_client)
            if function_check_success:
                logging.info(f"Index upload check succeeded for {len(ids)} items.")
            else:
                logging.error(f"Index upload check failed for {len(ids)} items.")
                errors.append("Failed to verify data was uploaded")

        values.append(
            {
                "recordId": record_id,
                "identifiers": ids,
                "errors": errors,
                "warnings": [],
            }
        )

    response_body = {"values": values}

    logging.info(f"Python HTTP trigger function created {len(data)} index items.")

    response = func.HttpResponse(
        json.dumps(response_body, default=lambda obj: obj.__dict__)
    )
    response.headers["Content-Type"] = "application/json"
    return response


def get_request_schema():
    """Retrieve the request schema from path."""
    with open(REQUEST_SCHEMA_PATH) as f:
        schema = json.load(f)
    return schema


def populate_index(data, index_search_client):
    """
    Populate an index with data.

    Args:
        data: A list of objects each containing the following fields:
            - id: A unique identifier for the object
            - filename: The name of the file where the documents originated
            - content: The content of the document
            - contentVector: The embedding of the content

    Returns:
        None
    """
    index_search_client.upload_documents(documents=data)


def check_data(ids, index_search_client):
    """
    Check that data was uploaded to the index.

    Args:
        ids: A list of unique identifiers for the data

    Returns:
        bool: True if all the data was found in the index, False otherwise
    """
    time.sleep(1)
    count = 0
    for id in ids:
        filter = "id eq '{0}'".format(id)
        count += index_search_client.search(
            search_text="*", filter=filter, include_total_count=True
        ).get_count()
    logging.info(f"Found {count} items in the index.")
    return count == len(ids)


def cleanup_data(ids, index_search_client):
    """
    Remove data from the index.

    Args:
        ids: A list of unique identifiers for the data

    Returns:
        None
    """
    for id in ids:
        index_search_client.delete_documents(documents=[{"id": id}])
