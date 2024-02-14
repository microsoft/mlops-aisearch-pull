import requests
import shutil
import time

from azure.identity import DefaultAzureCredential
from azure.mgmt.web import WebSiteManagementClient
from mlops.common.config_utils import MLOpsConfig
from mlops.common.naming_utils import generate_experiment_name

# Define the path to the Azure function directory
APPLICATION_JSON_CONTENT_TYPE = 'application/json'
FUNCTION_API_VERSION = '2022-03-01'
FUNCTION_APP_URL = "https://{function_app_name}.scm.azurewebsites.net/api/zipdeploy"
FUNCTION_APP_URL_WITH_SLOT = "https://{function_app_name}-{slot}.scm.azurewebsites.net/api/zipdeploy"
FUNCTION_NAMES = ['CleanText']
FUNCTION_URL = "https://management.azure.com/subscriptions/{subscription_id}" \
    "/resourceGroups/{resource_group}" \
    "/providers/Microsoft.Web/sites/{function_app_name}" \
    "/functions/{function_name}"
FUNCTION_URL_WITH_SLOT = "https://management.azure.com/subscriptions/{subscription_id}" \
    "/resourceGroups/{resource_group}" \
    "/providers/Microsoft.Web/sites/{function_app_name}" \
    "/functions/{function_name}/slots/{slot}"
MANAGEMENT_SCOPE_URL = "https://management.azure.com/.default"
CUSTOM_SKILLS_DIR = "src/custom_skills"


def _get_function_app_name(credential: DefaultAzureCredential, sub_config: dict):
    # Get the function app name
    app_mgmt_client = WebSiteManagementClient(
        credential=credential,
        subscription_id=sub_config["subscription_id"])
    # The function app uses a GUID function so the name is unknown before hand. There is only one function app in the RG
    rag_app = list(
        filter(lambda n: n.resource_group == sub_config["resource_group_name"], app_mgmt_client.web_apps.list())
        )

    return rag_app[0].name


def _wait_for_functions_ready(sub_config: dict, function_app_name: str, access_token: str, slot: str):
    params = {
        'api-version': FUNCTION_API_VERSION
    }
    headers = {
        'Content-Type': APPLICATION_JSON_CONTENT_TYPE,
        'Accept': APPLICATION_JSON_CONTENT_TYPE,
        'Authorization': "Bearer {access_token}".format(access_token=access_token)
    }

    for function_name in FUNCTION_NAMES:
        if slot is None:
            url = FUNCTION_URL.format(
                subscription_id=sub_config["subscription_id"],
                resource_group=sub_config["resource_group_name"],
                function_app_name=function_app_name,
                function_name=function_name
            )
        else:
            url = FUNCTION_URL_WITH_SLOT.format(
                subscription_id=sub_config["subscription_id"],
                resource_group=sub_config["resource_group_name"],
                function_app_name=function_app_name,
                function_name=function_name,
                slot = slot
            )      
        status_code = 0
        status = "Custom skill {function_name} is not ready.".format(function_name=function_name)

        while status_code != 200:
            try:
                response = requests.get(url=url, params=params, headers=headers)
            except requests.exceptions.RequestException as e:
                print(e)
                raise SystemExit(e)

            status_code = response.status_code

            if status_code == 200:
                status = "Custom skill {function_name} is deployed.".format(function_name=function_name)

            print("Custom Skill status: {status}".format(status=status))

            if status_code == 200:
                break
            else:
                time.sleep(10)


def main():

    # initialize parameters from config.yaml
    config = MLOpsConfig()
    # subscription config section in yaml
    sub_config = config.sub_config

    credential = DefaultAzureCredential()

    # generate a slot name  for the functions based on the branch name
    slot_name = generate_experiment_name("skills")

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
        url = FUNCTION_APP_URL.format(function_app_name = function_app_name)
    else:
        url = FUNCTION_APP_URL_WITH_SLOT.format(function_app_name = function_app_name, slot = slot_name)

    try:
        # Send a POST request to the Azure function app to deploy the zip file
        response = requests.post(url, headers=headers, data = payload)
    except requests.exceptions.RequestException as e:
        print(e)
        raise SystemExit(e)

    if response.status_code not in [200, 202]:
        print("Deployment to {function_app_name} was not successful.".format(function_app_name=function_app_name))
        raise SystemExit("Deployment failed")

    _wait_for_functions_ready(sub_config, function_app_name=function_app_name, access_token=access_token, slot = slot_name)

    # response.text is empty when successful, create our own success message on 200 or 202
    if (response.status_code == 200) or (response.status_code == 202):
        print(f"Deployment to {function_app_name} successful.")


if __name__ == "__main__":
    main()
