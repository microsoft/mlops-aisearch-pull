"""Implement tests for existing custom skills."""
import requests
import json


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
    request_file_path = "src/requests/toChunker.json"
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
        request_file_path = "src/requests/toEmbedder.json"
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
