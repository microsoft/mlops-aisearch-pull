import azure.functions as func
import os
import logging
import json
import jsonschema
import openai
from openai import AzureOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type
)

REQUEST_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "request_schema.json")


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Generate vector embeddings for a list of texts."""
    logging.info("Python HTTP trigger function processed a request.")

    request = req.get_json()

    try:
        jsonschema.validate(request, schema=get_request_schema())
    except jsonschema.exceptions.ValidationError as e:
        return func.HttpResponse("Invalid request: {0}".format(e), status_code=400)

    values = []
    for value in request["values"]:
        record_id = value["recordId"]

        chunk = value["data"]["chunk"]
        embedding = generate_embedding(chunk["page_content"])

        values.append(
            {
                "recordId": record_id,
                "data": {"embedding": embedding},
                "errors": None,
                "warnings": None,
            }
        )

    response_body = {"values": values}

    logging.info(
        f"Python HTTP trigger function created {len(chunk)} vector embeddings."
    )

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


def log_attempt_number(retry_state):
    """Log retry attempt."""
    row = retry_state.args[0]
    print(f"Rate Limit Exceeded! Retry Attempt #: {retry_state.attempt_number} | Chunk: {row}")


@retry(retry=retry_if_exception_type(openai.RateLimitError),
       wait=wait_random_exponential(min=1, max=60),
       stop=stop_after_attempt(10), after=log_attempt_number)
def generate_embedding(text):
    """
    Generate embeddings for text.

    Args:
        text: a block of text

    Returns:
        An object containing an 'contentVector' field
    """
    openai_client = AzureOpenAI(
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    )
    embedding_model_deployment = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

    embedding_response = openai_client.embeddings.create(
        input=text, model=embedding_model_deployment
    )

    return embedding_response.data[0].embedding
