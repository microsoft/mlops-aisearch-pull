"""This module contains a few utility methods that allow us to verify functions work as expected."""

import requests
import json


def get_app_settings(config: dict, index_name: str):
    """Get the function app settings."""
    return [
        {
            "name": "AZURE_OPENAI_API_KEY",
            "value": config.aoai_config["aoai_api_key"]
        },
        {
            "name": "AZURE_OPENAI_API_VERSION",
            "value": config.aoai_config["aoai_api_version"]
        },
        {
            "name": "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
            "value": config.aoai_config["aoai_embedding_model_deployment"]
        },
        {
            "name": "AZURE_OPENAI_ENDPOINT",
            "value": config.aoai_config["aoai_api_base"]
        },
        {
            "name": "AZURE_SEARCH_ENDPOINT",
            "value": config.acs_config["acs_api_base"]
        },
        {
            "name": "AZURE_SEARCH_API_KEY",
            "value": config.acs_config["acs_api_key"]
        },
        {
            "name": "AZURE_SEARCH_API_VERSION",
            "value": config.acs_config["acs_api_version"]
        },
        {
            "name": "AZURE_SEARCH_INDEX_NAME",
            "value": index_name
        },
        {
            "name": "AZURE_STORAGE_ACCOUNT_CONNECTION_STRING",
            "value": config.sub_config["storage_account_connection_string"]
        },
        {
            "name": "AZURE_STORAGE_CONTAINER_NAME",
            "value": config.get_flow_config("data")["storage_container"]
        }
    ]


def read_json_from_file(file_path):
    """Read a json file and return the contents as a dictionary."""
    with open(file_path, "r") as f:
        return json.load(f)


def test_chunker(url: str, headers: dict):
    """
    Test the chunker function.

    Args:
        url: The url of the function
        params: The query parameters
        headers: The headers

    Returns:
        The response body if successful, None otherwise
    """
    request_file_path = "./mlops/requests/toChunker.json"
    request_body = read_json_from_file(request_file_path)
    response = requests.post(url=url, headers=headers, json=request_body)

    if response.status_code == 200:
        # verify some things
        response_body = response.json()
        if len(response_body["values"][0]["data"]) == 4:
            print("Chunk test passed")
            return response_body
        else:
            print("Chunk test failed")
            print("Response:", response.text)
    else:
        print("Chunk Request failed with status code:", response.status_code)
        print("Response:", response.text)

    return None


def test_embedder(url: str, headers: dict, chunker_response=None):
    """
    Test the embedder function.

    Args:
        url: The url of the function
        params: The query parameters
        headers: The headers
        chunker_response: The response from the chunker function
                        - to be used if chaining validation functions

    Returns:
        The response body if successful, None otherwise
    """
    if chunker_response is None:
        request_file_path = "./mlops/requests/toEmbedder.json"
        request_body = read_json_from_file(request_file_path)
    else:
        request_body = chunker_response
    response = requests.post(url=url, headers=headers, json=request_body)
    if response.status_code == 200:
        # verify some things
        response_body = response.json()
        if len(response_body["values"][0]["data"]["embedding"]) == 1536:
            print("Embed test passed")
            return response_body
        else:
            print("Embed test failed")
            print("Response:", response.text)
    else:
        print("Embed Request failed with status code:", response.status_code)
        print("Response:", response.text)

    return None
