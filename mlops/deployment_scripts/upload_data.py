"""
Initialize blob storage with local data.

We assume that this code will be executed just once to prepare a blob container for experiments.
"""

from pathlib import Path
import argparse
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
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
            exit(-1)


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

    # getting data_pr section from the config (pr is a default environment)
    data_location_details = config.get_flow_config("data")

    local_folder = data_location_details["local_folder"]
    storage_container = data_location_details["storage_container"]

    _upload_ops_files(
        credential=credential,
        storage_account_name=storage_account_name,
        storage_container=storage_container,
        local_folder=local_folder,
    )


if __name__ == "__main__":
    main()
