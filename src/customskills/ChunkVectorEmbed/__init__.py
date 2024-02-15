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
        filename = value["data"]["filename"]

        chunks = chunk_pdf_file_from_azure(filename)
        embeddings, ids = generate_embeddings(chunks, filename)
        populate_index(embeddings)

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
        f"Python HTTP trigger function created {len(chunks)} chunks."
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

def chunk_pdf_file_from_azure(
        file_name: str,
        chunk_size: int = 1000,
        overlap_size: int = 100
):
    """
    Splits a PDF file into chunks of text

    Args:
        file_name: The name of the PDF file in Azure Blob Storage
        chunk_size: The size of the chunks
        overlap_size: The size of the overlap between chunks

    Returns:
        A list of Documents, each containing a 'page_content' chunk of text
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap_size)
    loader = AzureBlobStorageFileLoader(
        conn_str=os.environ.get("AZURE_STORAGE_ACCOUNT_CONNECTION_STRING"),
        container=os.environ.get("AZURE_STORAGE_CONTAINER_NAME"),
        blob_name=file_name,
    )
    chunks = loader.load_and_split(text_splitter=text_splitter)
    return chunks

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
        embedding_response = openai_client.embeddings.create(input=doc.page_content, model=EMBEDDING_MODEL_DEPLOYMENT)
        id = str(uuid.uuid4())
        ids.append(id)
        embeddings.append({
            "id": id,
            "filename": filename,
            "content": doc.page_content,
            "contentVector": embedding_response.data[0].embedding
        })
    return embeddings, ids

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
