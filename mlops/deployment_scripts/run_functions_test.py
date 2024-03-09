from src.skills_tests import test_chunker, test_embedder


APPLICATION_JSON_CONTENT_TYPE = "application/json"


def _verify_function_works(function_app_name: str, slot: str, function_name: str):
    """Verify that the function is working properly based on function name."""
    headers = {
        "Content-Type": APPLICATION_JSON_CONTENT_TYPE,
        "Accept": APPLICATION_JSON_CONTENT_TYPE,
    }
    url = f"https://{function_app_name}-{slot}.azurewebsites.net/api/{function_name}"

    if function_name == "Chunk":
        return test_chunker(url, headers)
    elif function_name == "VectorEmbed":
        return test_embedder(url, headers)
    else:
        return True

def main():
    pass


if __name__ == "__main__":
    main()
