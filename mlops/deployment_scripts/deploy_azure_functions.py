"""Deploy Custom Skills to Azure into a slot or to production."""

import requests
import shutil
import time
import argparse

from azure.identity import DefaultAzureCredential
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.web.v2023_01_01.models import Site
from mlops.common.config_utils import MLOpsConfig
from mlops.common.naming_utils import generate_slot_name, generate_index_name
from mlops.common.function_utils import (
    test_chunker,
    test_embedder,
    get_app_settings,
)

# Define the path to the Azure function directory
APPLICATION_JSON_CONTENT_TYPE = "application/json"
FUNCTION_API_VERSION = "2022-03-01"
FUNCTION_APP_URL = "https://{function_app_name}.scm.azurewebsites.net/api/zipdeploy"
FUNCTION_APP_URL_WITH_SLOT = (
    "https://{function_app_name}-{slot}.scm.azurewebsites.net/api/zipdeploy"
)
FUNCTION_NAMES = ["Chunk", "VectorEmbed"]
FUNCTION_URL = (
    "https://management.azure.com/subscriptions/{subscription_id}"
    "/resourceGroups/{resource_group}"
    "/providers/Microsoft.Web/sites/{function_app_name}"
    "/functions/{function_name}"
)
FUNCTION_URL_WITH_SLOT = (
    "https://management.azure.com/subscriptions/{subscription_id}"
    "/resourceGroups/{resource_group}"
    "/providers/Microsoft.Web/sites/{function_app_name}"
    "/slots/{slot}/functions/{function_name}"
)
MANAGEMENT_SCOPE_URL = "https://management.azure.com/.default"
CUSTOM_SKILLS_DIR = "src/custom_skills"


def _get_function_app_name(credential: DefaultAzureCredential, sub_config: dict):
    # Get the function app name
    app_mgmt_client = WebSiteManagementClient(
        credential=credential, subscription_id=sub_config["subscription_id"]
    )
    # The function app uses a GUID function so the name is unknown before hand. There is only one function app in the RG
    rag_app = list(
        filter(
            lambda n: n.resource_group == sub_config["resource_group_name"],
            app_mgmt_client.web_apps.list(),
        )
    )

    return rag_app[0].name


def _create_or_update_deployment_slot(
    credential: DefaultAzureCredential,
    sub_config: dict,
    func_name: str,
    slot: str,
    app_settings: list,
):
    app_mgmt_client = WebSiteManagementClient(
        credential=credential, subscription_id=sub_config["subscription_id"]
    )

    rag_app = list(
        filter(
            lambda n: n.resource_group == sub_config["resource_group_name"],
            app_mgmt_client.web_apps.list(),
        )
    )

    # site_config = {"appSettings": app_settings}

    ops_call = app_mgmt_client.web_apps.begin_create_or_update_slot(
        sub_config["resource_group_name"],
        func_name,
        slot,
        Site(location=rag_app[0].location),
    )
    while not ops_call.done():
        print(f"Updating the slot: {slot}")
        time.sleep(10)
    print("Slot has been updated")


def _wait_for_functions_ready(
    sub_config: dict, function_app_name: str, access_token: str, slot: str
):
    params = {"api-version": FUNCTION_API_VERSION}
    headers = {
        "Content-Type": APPLICATION_JSON_CONTENT_TYPE,
        "Accept": APPLICATION_JSON_CONTENT_TYPE,
        "Authorization": "Bearer {access_token}".format(access_token=access_token),
    }

    for function_name in FUNCTION_NAMES:
        if slot is None:
            url = FUNCTION_URL.format(
                subscription_id=sub_config["subscription_id"],
                resource_group=sub_config["resource_group_name"],
                function_app_name=function_app_name,
                function_name=function_name,
            )
        else:
            url = FUNCTION_URL_WITH_SLOT.format(
                subscription_id=sub_config["subscription_id"],
                resource_group=sub_config["resource_group_name"],
                function_app_name=function_app_name,
                function_name=function_name,
                slot=slot,
            )
        status_code = 0
        status = "Custom skill {function_name} is not ready.".format(
            function_name=function_name
        )

        print(f"Checking url: {url}")

        while status_code != 200:
            try:
                response = requests.get(url=url, params=params, headers=headers)
            except requests.exceptions.RequestException as e:
                print(e)
                raise SystemExit(e)

            status_code = response.status_code

            if status_code == 200:
                status = "Custom skill {function_name} is deployed.".format(
                    function_name=function_name
                )

            print("Custom Skill status: {status}".format(status=status))

            if status_code == 200:
                break
            else:
                time.sleep(10)

        if not _verify_function_works(url, params, headers, function_name):
            raise SystemExit(f"Function {function_name} is not working properly.")


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
    """Create a deployment of cognitive skills."""
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
    sub_config = config.sub_config

    credential = DefaultAzureCredential()

    # generate a slot name  for the functions based on the branch name
    if args.ignore_slot is False:
        slot_name = generate_slot_name()
    else:
        slot_name = None

    # Generate access token header
    access_token = credential.get_token(MANAGEMENT_SCOPE_URL).token
    headers = {
        "Content-Type": "application/zip",
        "Authorization": "Bearer {access_token}".format(access_token=access_token),
    }

    # Create a zip file of the Custom Skills directory
    zip_filename = shutil.make_archive(
        base_name="__customskills",
        format="zip",
        root_dir=CUSTOM_SKILLS_DIR,
    )

    # Define the payload for the REST API call
    with open(zip_filename, "rb") as f:
        payload = f.read()

    # URL for Azure Function App ZIP file deployments
    function_app_name = _get_function_app_name(credential, sub_config)

    if slot_name is None:
        url = FUNCTION_APP_URL.format(function_app_name=function_app_name)
    else:
        app_settings = get_app_settings(config, generate_index_name())
        _create_or_update_deployment_slot(
            credential, sub_config, function_app_name, slot_name, app_settings
        )
        url = FUNCTION_APP_URL_WITH_SLOT.format(
            function_app_name=function_app_name, slot=slot_name
        )
    print(f"Deploying to: {url}")
    try:
        # Send a POST request to the Azure function app to deploy the zip file
        response = requests.post(url, headers=headers, data=payload)
    except requests.exceptions.RequestException as e:
        print(e)
        raise SystemExit(e)

    if response.status_code not in [200, 202]:
        print(
            "Deployment to {function_app_name} was not successful.".format(
                function_app_name=function_app_name
            )
        )
        raise SystemExit("Deployment failed")

    _wait_for_functions_ready(
        sub_config,
        function_app_name=function_app_name,
        access_token=access_token,
        slot=slot_name,
    )

    # response.text is empty when successful, create our own success message on 200 or 202
    if (response.status_code == 200) or (response.status_code == 202):
        print(f"Deployment to {function_app_name} successful.")


if __name__ == "__main__":
    main()
