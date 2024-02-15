import azure.functions as func
import os
import logging
import json
import jsonschema
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

app = func.FunctionApp()

REQUEST_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "request_schema.json")


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Uploads documents to an Azure Cognitive Search index"""

    logging.info("Python HTTP trigger function processed a request.")

    request = req.get_json()

    try:
        jsonschema.validate(request, schema=get_request_schema())
    except jsonschema.exceptions.ValidationError as e:
        return func.HttpResponse("Invalid request: {0}".format(e), status_code=400)

    values = []
    for value in request["values"]:
        record_id = value["recordId"]
        data = value["data"]
        ids = value["identifiers"]

        populate_index(data)

        values.append(
            {
                "recordId": record_id,
                "identifiers": ids,
                "errors": None,
                "warnings": None,
            }
        )

    response_body = {"values": values}

    logging.info(
        f"Python HTTP trigger function created {len(data)} index items."
    )

    response = func.HttpResponse(
        json.dumps(response_body, default=lambda obj: obj.__dict__)
    )
    response.headers["Content-Type"] = "application/json"
    return response


def get_request_schema():
    """Retrieves the request schema from path"""

    with open(REQUEST_SCHEMA_PATH) as f:
        schema = json.load(f)
    return schema


def populate_index(data):
    """
    Populates an index with data

    Args:
        data: A list of objects each containing the following fields:
            - id: A unique identifier for the object
            - filename: The name of the file where the documents originated
            - content: The content of the document
            - contentVector: The embedding of the content

    Returns:
        None
    """
    INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX_NAME")
    index_search_client = SearchClient(
        os.environ.get("AZURE_SEARCH_ENDPOINT"),
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(os.environ.get("AZURE_SEARCH_API_KEY")),
    )

    index_search_client.upload_documents(documents=data)
