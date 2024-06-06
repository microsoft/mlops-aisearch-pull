"""
This module invokes a set of functions that test just deployed custom skills.

The reason to have these tests is to validate functions using small samples prior
creating any kind of indexes and skillsets. This script is a part of DevOps pipelines.
"""

import argparse
from src.skills_tests import test_chunker, test_embedder
from mlops.common.config_utils import MLOpsConfig
from mlops.common.naming_utils import generate_slot_name
from mlops.common.function_utils import get_function_key
from azure.identity import DefaultAzureCredential

APPLICATION_JSON_CONTENT_TYPE = "application/json"


def _verify_function_works(
    credentials: DefaultAzureCredential,
    subscription_id: str,
    resource_group_name: str,
    function_app_name: str,
    function_name: str,
    slot: str | None,
):
    """Verify that the function is working properly based on function name."""
    headers = {
        "Content-Type": APPLICATION_JSON_CONTENT_TYPE,
        "Accept": APPLICATION_JSON_CONTENT_TYPE,
    }
    function_key = get_function_key(
        credentials,
        subscription_id,
        resource_group_name,
        function_app_name,
        function_name,
        slot,
    )
    if slot is None:
        url = f"https://{function_app_name}.azurewebsites.net/api/{function_name}?code={function_key}"
    else:
        url = f"https://{function_app_name}-{slot}.azurewebsites.net/api/{function_name}?code={function_key}"

    if function_name == "Chunk":
        return test_chunker(url, headers)
    elif function_name == "Vector_Embed":
        return test_embedder(url, headers)
    else:
        return True


def main():
    """Initiate test for all available custom skills in the list."""
    # We need to pass ignore_slot to deploy into the default one
    # this option is needed for CI Build
    parser = argparse.ArgumentParser(description="Parameter parser")
    parser.add_argument(
        "--ignore_slot",
        action="store_true",
        default=False,
        help="allows to publish to the production slot",
    )
    args = parser.parse_args()

    # initialize parameters from config.yaml
    config = MLOpsConfig()

    # subscription config section in yaml
    subscription_id = config.sub_config["subscription_id"]
    resource_group = config.sub_config["resource_group_name"]

    # functions_config contains a section with function settings
    function_app_name = config.functions_config["function_app_name"]

    credential = DefaultAzureCredential()
    # functions_config contains a section with function settings

    # generate a slot name  for the functions based on the branch name
    if args.ignore_slot is False:
        slot_name = generate_slot_name()
    else:
        slot_name = None
    function_names = config.functions_config["function_names"]

    for f_name in function_names:
        _verify_function_works(
            credential,
            subscription_id,
            resource_group,
            function_app_name,
            f_name,
            slot_name,
        )


if __name__ == "__main__":
    main()
