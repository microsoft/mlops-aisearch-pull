import json
import logging
import os

import azure.functions as func
import jsonschema
import string
import unicodedata

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
# schema
REQUEST_SCHEMA_FILENAME = "request_schema.json"
DOUBLE_ARROWS_SET = set("»")
PUNCTUATION_SET = set(string.punctuation)


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request")

    try:
        body = req.get_json()
        logging.info(f"Body: {body}")
    except ValueError as e:
        logging.info(e)
        return func.HttpResponse("Body is not valid JSON.", status_code=400)

    with open(os.path.join(DIR_PATH, REQUEST_SCHEMA_FILENAME), "r") as f:
        request_schema = json.load(f)

    try:
        jsonschema.validate(instance=body, schema=request_schema)
        logging.info("Valid schema.")
    except jsonschema.exceptions.ValidationError as e:
        return func.HttpResponse("Invalid request: {0}".format(e), status_code=400)

    formatted_results = []
    for v in body["values"]:
        # extract keyphrases
        page_text = v["data"]["content"]
        logging.info(f"Text: {page_text}")

        # Remove/replace special characters
        cleaned_text = clean_text(page_text)
        logging.info(f"After punctuation: {cleaned_text}")

        formatted_results.append(
            {"recordId": v["recordId"], "data": {"cleanText": cleaned_text}}
        )

    # turn all the results into a json string
    return_value = json.dumps({"values": formatted_results}, default=vars)
    logging.info(f"Formatted results: {return_value}")

    return func.HttpResponse(
        return_value,
        mimetype="application/json",
    )


def should_char_be_removed(ch: chr) -> bool:
    return unicodedata.category(ch) == "Mn" or ch in DOUBLE_ARROWS_SET


def clean_text(text: str) -> str:
    normalized_text = unicodedata.normalize("NFD", text)
    results = "".join(
        " " if ch in PUNCTUATION_SET else ch.lower()
        for ch in normalized_text
        if not should_char_be_removed(ch)
    )
    results = unicodedata.normalize("NFC", results)

    return results
