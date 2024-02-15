import azure.functions as func
import os
import logging
import json
import jsonschema
import uuid
from openai import AzureOpenAI
from langchain_community.document_loaders import AzureBlobStorageFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient

app = func.FunctionApp()

REQUEST_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "request_schema.json")

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    request = req.get_json()

    try:
        jsonschema.validate(request, schema= get_request_schema())
    except jsonschema.exceptions.ValidationError as e:
        return func.HttpResponse("Invalid request: {0}".format(e), status_code=400)

    values = []
    for value in request["values"]:
        recordId = value["recordId"]
        filename = value["filename"]

        chunks = value["data"]
        embeddings, ids = generate_embeddings(chunks, filename)

        values.append(
            {
                "recordId": recordId,
                "identifiers": ids,
                "data": embeddings,
                "errors": None,
                "warnings": None,
            }
        )

    response_body = {"values": values}

    logging.info(
        f"Python HTTP trigger function created {len(chunks)} vector embeddings."
    )

    response = func.HttpResponse(
        json.dumps(response_body, default=lambda obj: obj.__dict__)
    )
    response.headers["Content-Type"] = "application/json"
    return response


def get_request_schema():
    with open(REQUEST_SCHEMA_PATH) as f:
        schema = json.load(f)
    return schema


def generate_embeddings(documents, filename):
    """
    Generates embeddings for a list of documents

    Args:
        documents: A list of Documents

    Returns:
        A list of Documents, each containing an 'contentVector' field
    """
    openai_client = AzureOpenAI(
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
    )
    EMBEDDING_MODEL_DEPLOYMENT = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    embeddings = []
    ids = []
    for doc in documents:
        embedding_response = openai_client.embeddings.create(input=doc["page_content"], model=EMBEDDING_MODEL_DEPLOYMENT)
        id = str(uuid.uuid4())
        ids.append(id)
        embeddings.append({
            "id": id,
            "filename": filename,
            "content": doc["page_content"],
            "contentVector": embedding_response.data[0].embedding
        })
    return embeddings, ids
