import azure.functions as func
import os
import logging
import json
import jsonschema
from azure.identity import DefaultAzureCredential
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader

from azure.storage.blob import BlobServiceClient


REQUEST_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "request_schema.json")


def function_chunk(req: func.HttpRequest) -> func.HttpResponse:
    """Divide document into chunks of text."""
    logging.info("Python HTTP trigger function processed a request.")

    request = req.get_json()

    try:
        jsonschema.validate(request, schema=_get_request_schema())
    except jsonschema.exceptions.ValidationError as e:
        return func.HttpResponse("Invalid request: {0}".format(e), status_code=400)

    values = []
    for value in request["values"]:
        record_id = value["recordId"]
        filename = value["data"]["filename"]

        chunks = _chunk_pdf_file_from_azure2(filename)

        values.append(
            {
                "recordId": record_id,
                "data": {"chunks": chunks},
                "errors": None,
                "warnings": None,
            }
        )

    response_body = {"values": values}

    logging.info(f"Python HTTP trigger function created {len(chunks)} chunks.")

    response = func.HttpResponse(
        json.dumps(response_body, default=lambda obj: obj.__dict__)
    )
    response.headers["Content-Type"] = "application/json"
    return response


def _get_request_schema():
    """Retrieve the request schema from path."""
    with open(REQUEST_SCHEMA_PATH) as f:
        schema = json.load(f)
    return schema


def _chunk_pdf_file_from_azure2(
    file_name: str, chunk_size: int = 1000, overlap_size: int = 100
):
    """
    Split a PDF file into chunks of text.

    Args:
        file_name: The name of the PDF file in Azure Blob Storage
        chunk_size: The size of the chunks
        overlap_size: The size of the overlap between chunks

    Returns:
        A list of Documents, each containing a 'page_content' chunk of text
    """
    account_name = os.environ.get("AZURE_STORAGE_ACCOUNT_NAME")
    container = os.environ.get("AZURE_STORAGE_CONTAINER_NAME")

    credential = DefaultAzureCredential()

    blob_service_client = BlobServiceClient(
        account_url=f"https://{account_name}.blob.core.windows.net",
        credential=credential)

    container_client = blob_service_client.get_container_client(container)

    blob_client = container_client.get_blob_client(blob=file_name)
    with open(f"/tmp/{file_name}", "wb") as file:
        file.write(blob_client.download_blob().readall())

    loader = PyPDFLoader(f"/tmp/{file_name}")
    pages = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=overlap_size
    )

    chunks = text_splitter.split_documents(pages)

    return chunks
