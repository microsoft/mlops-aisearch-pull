"""
This module contains functions to create index, indexer, skillset and datasource.

This module is the primary endpoint for experiments with AI Search service
"""

import requests
import time
import argparse

from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.mgmt.search import SearchManagementClient
from azure.search.documents.indexes import SearchIndexerClient
from azure.search.documents.indexes.models import SearchIndexerDataSourceConnection
from ..common.config_utils import MLOpsConfig
from ..common.naming_utils import (
    generate_index_name,
    generate_indexer_name,
    generate_data_source_name,
    generate_skillset_name,
    generate_slot_name
)
from mlops.common.function_utils import get_function_key
from mlops.common.ai_search_utils import generate_indexer


APPLICATION_JSON_CONTENT_TYPE = "application/json"
MANAGEMENT_SCOPE_URL = "https://management.azure.com/.default"


def _create_or_update_search_index(
    aoai_config: dict,
    search_service_name: str,
    index_name: str,
    file_name: str,
    search_admin_key: str,
    api_version: str,
) -> None:

    # Use the REST API, there is a bug in the Search SDK that prevents creating the Vector field correctly
    index_url = (
        f"https://{search_service_name}.search.windows.net/indexes('{index_name}')"
    )
    print(f"index name is {index_name}")
    params = {"api-version": api_version, "allowIndexDowntime": "true"}
    headers = {
        "Content-Type": APPLICATION_JSON_CONTENT_TYPE,
        "Accept": APPLICATION_JSON_CONTENT_TYPE,
        "Prefer": "true",
        "api-key": search_admin_key,
    }
    with open(file_name) as index_file:
        index_def = index_file.read()

    index_def = index_def.replace("{openai_api_endpoint}", aoai_config["aoai_api_base"])
    index_def = index_def.replace(
        "{openai_embedding_deployment_name}",
        aoai_config["aoai_embedding_model_deployment"],
    )
    index_def = index_def.replace("{openai_api_key}", aoai_config["aoai_api_key"])
    index_def = index_def.replace("{openai_embedding_model}", aoai_config["aoai_embedding_model_deployment"])

    response = requests.put(
        url=index_url, data=index_def, params=params, headers=headers
    )

    if response.status_code not in [200, 201, 204]:
        raise Exception(response.content)


def _create_or_update_skillset(skillset: dict,
                               skillset_name: str,
                               search_service_name: str,
                               search_admin_key: str,
                               api_version: str) -> None:
    # Using the rest API because the SDK doesn't support indexProjections
    skillset_url = (
        f"https://{search_service_name}.search.windows.net/skillsets/{skillset_name}"
    )
    params = {"api-version": api_version}
    headers = {
        "Content-Type": APPLICATION_JSON_CONTENT_TYPE,
        "Accept": APPLICATION_JSON_CONTENT_TYPE,
        "Prefer": "true",
        "api-key": search_admin_key,
    }

    response = requests.put(
        url=skillset_url, data=skillset, params=params, headers=headers
    )

    if response.status_code not in [200, 201, 204]:
        raise Exception(response.content)


def _get_storage_conn_string(
    subscription_id: str,
    storage_account_name: str,
    resource_group_name: str,
) -> str:
    conn_string = f"ResourceId=/subscriptions/{subscription_id}" \
        f"/resourceGroups/{resource_group_name}/providers/Microsoft.Storage" \
        f"/storageAccounts/{storage_account_name};"

    return conn_string


def _get_identity_resource(
    subscription_id: str,
    resource_group_name: str,
    managed_identity_name: str
) -> str:
    resource_string = f"/subscriptions/{subscription_id}/resourcegroups/{resource_group_name}" \
        f"/providers/Microsoft.ManagedIdentity/userAssignedIdentities/{managed_identity_name}"

    return resource_string


def _generate_data_source_connection(
    connection_name: str, file_name: str, conn_string: str, user_identity_resource: str, container: str
):
    print(user_identity_resource)
    with open(file_name) as data_source_file:
        data_source_def = data_source_file.read()

    data_source_def = data_source_def.replace("{conn_string}", conn_string)
    data_source_def = data_source_def.replace("{container_name}", container)
    data_source_def = data_source_def.replace("{name}", connection_name)
    data_source_def = data_source_def.replace("{user_identity_resource}", user_identity_resource)
    data_source_connection = SearchIndexerDataSourceConnection.deserialize(
        data_source_def, APPLICATION_JSON_CONTENT_TYPE
    )
    # I don't know why this is necessary, the connection string is in the credentials, it's not happy without it
    data_source_connection.connection_string = conn_string

    return data_source_connection


def _generate_skillset(
    name: str,
    file_name: str,
    credentials,
    subscription_id: str,
    resource_group_name: str,
    index_name: str,
    function_app_name: str,
    function_names: list,
    slot: str
) -> object:

    # Get the config
    with open(file_name) as skillset_file:
        skillset_def = skillset_file.read()

    skillset_def = skillset_def.replace("{name}", name)
    skillset_def = skillset_def.replace("{index_name}", index_name)
    for func_name in function_names:
        function_key = get_function_key(
            credentials,
            subscription_id,
            resource_group_name,
            function_app_name,
            func_name,
            slot,
        )
        if slot is None:
            url = f"https://{function_app_name}.azurewebsites.net/api/{func_name}?code={function_key}"
        else:
            url = f"https://{function_app_name}-{slot}.azurewebsites.net/api/{func_name}?code={function_key}"

        skillset_def = skillset_def.replace(f"{{{func_name}_url}}", url)

    return skillset_def


def _wait_for_document_indexer(indexer_client: SearchIndexerClient, indexer_name: str):
    status = "Indexer {document_indexer_name} not started yet".format(
        document_indexer_name=indexer_name
    )

    while (
        indexer_client.get_indexer_status(indexer_name).last_result is None
        or (
            status := indexer_client.get_indexer_status(indexer_name).last_result.status
        )
        != "success"
    ):
        print("Document indexer status: {status}".format(status=status))

        if status == "transientFailure":
            break

        time.sleep(10)


def main():
    """Create an indexer based on the configuration parameters and branch name."""
    credential = DefaultAzureCredential()

    """Upload data to a desired blob container."""
    parser = argparse.ArgumentParser(description="Parameter parser")
    parser.add_argument(
        "--stage",
        default="pr",
        help="stage to find parameters: pr, dev",
    )
    parser.add_argument(
        "--ignore_slot",
        action="store_true",
        default=False,
        help="allows to use functions from production slot",
    )
    args = parser.parse_args()

    # initialize parameters from config.yaml
    config = MLOpsConfig(environment=args.stage)

    # subscription config section in yaml
    sub_config = config.sub_config
    acs_config = config.acs_config
    aoai_config = config.aoai_config
    func_config = config.functions_config

    index_name = generate_index_name()
    indexer_name = generate_indexer_name()
    skillset_name = generate_skillset_name()
    datasource_name = generate_data_source_name()

    search_management_client = SearchManagementClient(
        credential=credential, subscription_id=sub_config["subscription_id"]
    )

    search_admin_key = search_management_client.admin_keys.get(
        resource_group_name=sub_config["resource_group_name"],
        search_service_name=acs_config["acs_service_name"],
    ).primary_key

    # Create the full document index
    _create_or_update_search_index(
        aoai_config,
        search_service_name=acs_config["acs_service_name"],
        index_name=index_name,
        file_name=acs_config["acs_document_index_file"],
        search_admin_key=search_admin_key,
        api_version=acs_config["acs_api_version"],
    )

    conn_string = _get_storage_conn_string(
        sub_config["subscription_id"],
        sub_config["storage_account_name"],
        sub_config["resource_group_name"],
    )

    key_credential = AzureKeyCredential(search_admin_key)
    search_indexer_client = SearchIndexerClient(
        acs_config["acs_api_base"], key_credential
    )

    # getting data_pr section from the config (pr is a default environment)
    data_location_details = config.get_flow_config("data")

    storage_container = data_location_details["storage_container"]

    # Create the full document Data Source for the Indexer
    document_data_source_connection = _generate_data_source_connection(
        generate_data_source_name(),
        file_name=acs_config["acs_document_data_source"],
        conn_string=conn_string,
        user_identity_resource=_get_identity_resource(
            sub_config["subscription_id"],
            sub_config["resource_group_name"],
            sub_config["managed_identity_name"],
        ),
        container=storage_container,
    )
    search_indexer_client.create_or_update_data_source_connection(
        data_source_connection=document_data_source_connection
    )

    # generate a slot name  for the functions based on the branch name
    if args.ignore_slot is False:
        slot_name = generate_slot_name()
    else:
        slot_name = None

    # Create full document Skillset
    document_skillset = _generate_skillset(
        skillset_name,
        acs_config["acs_document_skillset_file"],
        credential,
        sub_config["subscription_id"],
        sub_config["resource_group_name"],
        index_name,
        func_config["function_app_name"],
        func_config["function_names"],
        slot_name
    )

    _create_or_update_skillset(
        document_skillset,
        skillset_name,
        search_service_name=acs_config["acs_service_name"],
        search_admin_key=search_admin_key,
        api_version=acs_config["acs_api_version"]
    )
    # Create the full document Indexer
    document_indexer = generate_indexer(
        acs_config["acs_document_indexer_file"],
        {
            "name": indexer_name,
            "data_source_name": datasource_name,
            "index_name": index_name,
            "skillset_name": skillset_name
        }
    )
    search_indexer_client.create_or_update_indexer(indexer=document_indexer)

    # Wait for the full document indexer to complete.
    _wait_for_document_indexer(search_indexer_client, generate_indexer_name())


if __name__ == "__main__":
    main()
