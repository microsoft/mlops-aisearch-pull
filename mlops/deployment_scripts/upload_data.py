"""
Initialize blob storage with local data.

We assume that this code will be executed just once to prepare a blob container for experiments.
"""

import base64
import json
import uuid
from pathlib import Path
import argparse
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.core.exceptions import ResourceExistsError
from mlops.common.config_utils import MLOpsConfig


STORAGE_ACCOUNT_URL = "https://{storage_account_name}.blob.core.windows.net"
STORAGE_ROLE_NAME = "Storage Blob Data Contributor"


def _upload_ops_files(
    credential: DefaultAzureCredential,
    storage_account_name: str,
    storage_container: str,
    local_folder: str,
):

    account_url = STORAGE_ACCOUNT_URL.format(storage_account_name=storage_account_name)
    blob_service_client = BlobServiceClient(
        account_url=account_url, credential=credential
    )
    blob_container_client = blob_service_client.get_container_client(storage_container)

    if not blob_container_client.exists():
        print(f"Creating {storage_container} container.")
        blob_container_client.create_container()
        print("Done.")

    for file in Path().rglob(f"{local_folder}/*.pdf"):
        # construct blob name from file path

        # everything rather than local_folder
        file_subpath = str(file).split(f"{local_folder}/")[1]

        # generate a unique name of the file
        file_name = file_subpath.replace("/", "_")

        try:
            print(f"Ready to copy: {str(file)} to {file_name}.")
            with open(file=str(file), mode="rb") as data:
                blob_container_client.upload_blob(
                    name=file_name, data=data, overwrite=True
                )
            print("Done.")
        except Exception as e:
            print(f"Exception uploading file name {file_name}: {e}")
            break


def _get_user_object_id(credential: DefaultAzureCredential):
    token = credential.get_token("https://management.azure.com/", scopes=["user.read"])

    # decode token information to get user object id
    base64_meta_data = token.token.split(".")[1].encode("utf-8") + b"=="
    json_bytes = base64.decodebytes(base64_meta_data)
    json_string = json_bytes.decode("utf-8")
    json_dict = json.loads(json_string)
    current_user_id = json_dict["oid"]
    return current_user_id


def _create_storage_role_assignment(
    credential: DefaultAzureCredential,
    subscription_id: str,
    resource_group: str,
    storage_account_name: str,
):

    auth_client = AuthorizationManagementClient(
        DefaultAzureCredential(), subscription_id
    )

    scope = (
        f"/subscriptions/{subscription_id}/resourceGroups/"
        f"{resource_group}/providers/Microsoft.Storage/storageAccounts"
        f"/{storage_account_name}"
    )

    # Get built-in role as a RoleDefinition object
    roles = list(
        auth_client.role_definitions.list(
            scope, filter="roleName eq '{}'".format(STORAGE_ROLE_NAME)
        )
    )
    assert len(roles) == 1
    contributor_role = roles[0]

    # Create role assignment
    role_assignment_props = {
        "role_definition_id": contributor_role.id,
        "principal_id": _get_user_object_id(credential=credential),
    }
    try:
        auth_client.role_assignments.create(scope, uuid.uuid4(), role_assignment_props)
    except ResourceExistsError:
        print("Role assignment already exists.")


def main():
    """Upload data to a desired blob container."""
    parser = argparse.ArgumentParser(description="Parameter parser")
    parser.add_argument(
        "--stage",
        default="pr",
        help="stage to find parameters: pr, dev",
    )
    args = parser.parse_args()

    # initialize parameters from config.yaml
    config = MLOpsConfig(environment=args.stage)

    # subscription config section in yaml
    sub_config = config.sub_config

    credential = DefaultAzureCredential()

    storage_account_name = sub_config["storage_account_name"]
    # subscription_id = sub_config["subscription_id"]
    # resource_group_name = sub_config["resource_group_name"]

    # getting data_pr section from the config (pr is a default environment)
    data_location_details = config.get_flow_config("data")

    local_folder = data_location_details["local_folder"]
    storage_container = data_location_details["storage_container"]

    # _create_storage_role_assignment(
    #     credential, subscription_id, resource_group_name, storage_account_name
    # )

    _upload_ops_files(
        credential=credential,
        storage_account_name=storage_account_name,
        storage_container=storage_container,
        local_folder=local_folder,
    )


if __name__ == "__main__":
    main()
