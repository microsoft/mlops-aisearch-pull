import azure.functions as func
import os
import logging
import json
import jsonschema
from langchain_community.document_loaders import AzureBlobStorageFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


REQUEST_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "request_schema.json")


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Divide document into chunks of text."""
    logging.info("Python HTTP trigger function processed a request.")

    request = req.get_json()

    try:
        jsonschema.validate(request, schema=get_request_schema())
    except jsonschema.exceptions.ValidationError as e:
        return func.HttpResponse("Invalid request: {0}".format(e), status_code=400)

    values = []
    for value in request["values"]:
        record_id = value["recordId"]
        filename = value["data"]["filename"]

        chunks = chunk_pdf_file_from_azure(filename)

        values.append(
            {
                "recordId": record_id,
                "filename": filename,
                "data": chunks,
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


def get_request_schema():
    """Retrieve the request schema from path."""
    with open(REQUEST_SCHEMA_PATH) as f:
        schema = json.load(f)
    return schema


def chunk_pdf_file_from_azure(
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
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=overlap_size
    )
    loader = AzureBlobStorageFileLoader(
        conn_str=os.environ.get("AZURE_STORAGE_ACCOUNT_CONNECTION_STRING"),
        container=os.environ.get("AZURE_STORAGE_CONTAINER_NAME"),
        blob_name=file_name,
    )
    chunks = loader.load_and_split(text_splitter=text_splitter)
    return chunks
