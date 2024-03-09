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
    get_app_settings,
)

# Define the path to the Azure function directory
APPLICATION_JSON_CONTENT_TYPE = "application/json"
FUNCTION_API_VERSION = "2022-03-01"
DEPLOYMENT_APP_URL = "https://{function_app_name}.scm.azurewebsites.net/api/zipdeploy"
DEPLOYMENT_APP_URL_WITH_SLOT = (
    "https://{function_app_name}-{slot}.scm.azurewebsites.net/api/zipdeploy"
)
MANAGEMENT_FUNCTION_URL = (
    "https://management.azure.com/subscriptions/{subscription_id}"
    "/resourceGroups/{resource_group}"
    "/providers/Microsoft.Web/sites/{function_app_name}"
    "/functions/{function_name}"
)
MANAGEMENT_FUNCTION_URL_WITH_SLOT = (
    "https://management.azure.com/subscriptions/{subscription_id}"
    "/resourceGroups/{resource_group}"
    "/providers/Microsoft.Web/sites/{function_app_name}"
    "/slots/{slot}/functions/{function_name}"
)
MANAGEMENT_SCOPE_URL = "https://management.azure.com/.default"
CUSTOM_SKILLS_DIR = "src/custom_skills"


def _create_or_update_deployment_slot(
    credential: DefaultAzureCredential,
    subsription_id: str,
    resource_group_name: str,
    func_name: str,
    slot: str,
):
    app_mgmt_client = WebSiteManagementClient(
        credential=credential, subscription_id=subsription_id
    )

    # look at existing app for a location
    rag_app = app_mgmt_client.web_apps.get(resource_group_name, func_name)

    ops_call = app_mgmt_client.web_apps.begin_create_or_update_slot(
        resource_group_name,
        func_name,
        slot,
        Site(location=rag_app.location),
    )
    while not ops_call.done():
        print(f"Updating the slot: {slot}")
        time.sleep(10)
    print("Slot has been updated")


def _wait_for_functions_ready(
    credential: DefaultAzureCredential,
    subscription_id: str,
    resource_group: str,
    function_app_name: str,
    function_names: list,
    slot: str
):
    access_token = credential.get_token(MANAGEMENT_SCOPE_URL).token
    params = {"api-version": FUNCTION_API_VERSION}
    headers = {
        "Content-Type": APPLICATION_JSON_CONTENT_TYPE,
        "Accept": APPLICATION_JSON_CONTENT_TYPE,
        "Authorization": "Bearer {access_token}".format(access_token=access_token),
    }

    for function_name in function_names:
        if slot is None:
            url = MANAGEMENT_FUNCTION_URL.format(
                subscription_id=subscription_id,
                resource_group=resource_group,
                function_app_name=function_app_name,
                function_name=function_name,
            )
        else:
            url = MANAGEMENT_FUNCTION_URL_WITH_SLOT.format(
                subscription_id=subscription_id,
                resource_group=resource_group,
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


def _deploy_functions(
        credential: DefaultAzureCredential,
        deployment_url: str,
        subscription_id: str,
        resource_group_name: str,
        func_name: str,
        slot_name: str,
        app_settings: dict
):
    app_mgmt_client = WebSiteManagementClient(
        credential=credential, subscription_id=subscription_id
    )

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


    # TODO: Implement as async with no waiting
    try:
        # Send a POST request to the Azure function app to deploy the zip file
        requests.post(deployment_url, headers=headers, data=payload)
    except requests.exceptions.RequestException as e:
        print("Request has been sent, but no response yet.")
        # raise SystemExit(e)

    print("Looking for an active deployment.")
    # look at existing app for a location
    deployment_slots = app_mgmt_client.web_apps.list_deployments_slot(
        resource_group_name, func_name, slot_name)
    
    current_slot = deployment_slots.next()
    id = current_slot.id.split("/")[-1]

    print(f"Deployment id: {id}")
    status = current_slot.status

    while status!=4:
        current_slot = app_mgmt_client.web_apps.get_deployment_slot(resource_group_name, func_name, id, slot_name)
        status = current_slot.status
        if status == 1:
            print("Deployment is in progress")
        elif status!=4:
            raise SystemExit(f"Unknown deployment status {status}")
        time.sleep(10)

    print("Updating Application settings.")
    existing_app_settings = app_mgmt_client.web_apps.list_application_settings_slot(
        resource_group_name,
        func_name,
        slot_name
    )

    existing_app_settings.properties.update(app_settings)

    app_mgmt_client.web_apps.update_application_settings_slot(
        resource_group_name,
        func_name,
        slot_name,
        existing_app_settings
    )

    print("Restarting the application.")
    app_mgmt_client.web_apps.restart_slot(resource_group_name, func_name, slot_name)


def main():
    """Create a deployment of cognitive skills."""

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
    subscription_id=config.sub_config["subscription_id"]
    resource_group=config.sub_config["resource_group_name"]

    # functions_config contains a section with function settings
    function_app_name = config.functions_config["function_app_name"]

    credential = DefaultAzureCredential()

    # generate a slot name  for the functions based on the branch name
    if args.ignore_slot is False:
        slot_name = generate_slot_name()
    else:
        slot_name = None

    # deploying or updating the slot
    if slot_name is None:
        deployment_url = DEPLOYMENT_APP_URL.format(function_app_name=function_app_name)
    else:
        app_settings = get_app_settings(config, generate_index_name())
        print("Creating a deployment slot.")
        _create_or_update_deployment_slot(
            credential, subscription_id, resource_group, function_app_name, slot_name
        )
        deployment_url = DEPLOYMENT_APP_URL_WITH_SLOT.format(
            function_app_name=function_app_name, slot=slot_name
        )

    print(f"Deploying to: {deployment_url}")

    _deploy_functions(
        credential, deployment_url, subscription_id, resource_group, function_app_name, slot_name, app_settings)
    
    _wait_for_functions_ready(
        credential,
        subscription_id,
        resource_group,
        function_app_name=function_app_name,
        function_names=config.functions_config["function_names"],
        slot=slot_name,
    )


if __name__ == "__main__":
    main()
