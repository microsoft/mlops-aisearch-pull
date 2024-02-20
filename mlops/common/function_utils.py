"""This module contains a few utility methods that allow us to verify functions work as expected"""
import requests
import json


def read_json_from_file(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def test_chunker(url: str, params: dict, headers: dict):
    request_file_path = "../requests/toChunker.json"
    request_body = read_json_from_file(request_file_path)
    response = requests.post(url=url, params=params, headers=headers, json=request_body)

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


def test_embedder(url: str, params: dict, headers: dict, chunker_response=None):
    if chunker_response is None:
        request_file_path = "../requests/toEmbedder.json"
        request_body = read_json_from_file(request_file_path)
    else:
        request_body = chunker_response
    response = requests.post(url=url, params=params, headers=headers, json=request_body)
    if response.status_code == 200:
        # verify some things
        response_body = response.json()
        if len(response_body["values"][0]["identifiers"]) == 4:
            print("Embed test passed")
            return response_body
        else:
            print("Embed test failed")
            print("Response:", response.text)
    else:
        print("Embed Request failed with status code:", response.status_code)
        print("Response:", response.text)

    return None


def test_uploader(url: str, params: dict, headers: dict, embedder_response=None):
    if embedder_response is None:
        request_file_path = "../requests/toUploader.json"
        request_body = read_json_from_file(request_file_path)
    else:
        request_body = embedder_response
        request_body["values"][0]["functionCheck"] = True
    response = requests.post(url=url, params=params, headers=headers, json=request_body)
    if response.status_code == 200:
        # verify some things
        response_body = response.json()
        if len(response_body["values"][0]["errors"]) == 0:
            print("Upload test passed")
            return response_body
        else:
            print("Upload test failed")
            print("Response:", response.text)
    else:
        print("Upload Request failed with status code:", response.status_code)
        print("Response:", response.text)

    return None
