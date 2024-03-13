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
from azure.mgmt.storage import StorageManagementClient
from azure.search.documents.indexes import SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndexer,
    SearchIndexerDataSourceConnection,
    SearchIndexerSkillset,
)
from ..common.config_utils import MLOpsConfig
from ..common.naming_utils import (
    generate_index_name,
    generate_indexer_name,
    generate_data_source_name,
    generate_skillset_name,
)


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
    print(f'index name is {index_name}')
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
    index_def = index_def.replace("{openai_embedding_deployment_name}", aoai_config["aoai_embedding_model_deployment"])
    index_def = index_def.replace("{openai_api_key}", aoai_config["aoai_api_key"])

    print(f'index_def is {index_def}')
    print(f'index_url is {index_url}')
    print(f'params is {params}')
    print(f'headers is {headers}')
    response = requests.put(
        url=index_url, data=index_def, params=params, headers=headers
    )

    if response.status_code not in [200, 201, 204]:
        raise Exception(response.content)


def _get_storage_conn_string(
    credential: DefaultAzureCredential,
    subscription_id: str,
    storage_account_name: str,
    resource_group_name: str,
) -> str:
    storage_client = StorageManagementClient(
        credential=credential, subscription_id=subscription_id
    )
    keys = storage_client.storage_accounts.list_keys(
        resource_group_name, storage_account_name
    )
    conn_string = (
        "DefaultEndpointsProtocol=https;AccountName={storage_account_name};"
        + "AccountKey={key};"
        + "EndpointSuffix=core.windows.net"
    ).format(storage_account_name=storage_account_name, key=keys.keys[0].value)

    return conn_string


def _generate_data_source_connection(
    connection_name: str, file_name: str, conn_string: str, container: str
):
    with open(file_name) as data_source_file:
        data_source_def = data_source_file.read()

    data_source_def = data_source_def.replace("{conn_string}", conn_string)
    data_source_def = data_source_def.replace("{container_name}", container)
    data_source_def = data_source_def.replace("{name}", connection_name)
    data_source_connection = SearchIndexerDataSourceConnection.deserialize(
        data_source_def, APPLICATION_JSON_CONTENT_TYPE
    )
    # I don't know why this is necessary, the connection string is in the credentials, it's not happy without it
    data_source_connection.connection_string = conn_string

    return data_source_connection


def _generate_skillset(
    name: str,
    file_name: str,
) -> SearchIndexerSkillset:

    # Get the config
    with open(file_name) as skillset_file:
        skillset_def = skillset_file.read()

    skillset_def = skillset_def.replace("{name}", name)
    skillset = SearchIndexerSkillset.deserialize(
        skillset_def, APPLICATION_JSON_CONTENT_TYPE
    )

    return skillset


def _generate_indexer(
    name: str,
    file_name: str,
    data_source_name: str,
    index_name: str,
    skillset_name: str,
    conn_string: str,
) -> SearchIndexer:

    with open(file_name) as indexer_file:
        indexer_def = indexer_file.read()

    indexer_def = indexer_def.replace("{conn_string}", conn_string)
    indexer_def = indexer_def.replace("{name}", name)
    indexer_def = indexer_def.replace("{data_source_name}", data_source_name)
    indexer_def = indexer_def.replace("{index_name}", index_name)
    indexer_def = indexer_def.replace("{skillset_name}", skillset_name)

    indexer = SearchIndexer.deserialize(indexer_def, APPLICATION_JSON_CONTENT_TYPE)

    return indexer


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
    """Create an experiment based on the configuration parameters and branch name."""
    credential = DefaultAzureCredential()

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
    acs_config = config.acs_config
    aoai_config = config.aoai_config

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
        credential,
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
        container=storage_container,
    )
    search_indexer_client.create_or_update_data_source_connection(
        data_source_connection=document_data_source_connection
    )

    # Create full document Skillset
    document_skillset = _generate_skillset(
        skillset_name, acs_config["acs_document_skillset_file"]
    )
    search_indexer_client.create_or_update_skillset(skillset=document_skillset)

    # Create the full document Indexer
    document_indexer = _generate_indexer(
        indexer_name,
        acs_config["acs_document_indexer_file"],
        datasource_name,
        index_name,
        skillset_name,
        conn_string,
    )
    search_indexer_client.create_or_update_indexer(indexer=document_indexer)

    # Wait for the full document indexer to complete.
    _wait_for_document_indexer(search_indexer_client, generate_indexer_name())


if __name__ == "__main__":
    main()
