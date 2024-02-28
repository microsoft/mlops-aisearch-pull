import os
import pathlib
import requests
import time

from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureCliCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.search import SearchManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.web import WebSiteManagementClient
from azure.search.documents.indexes import SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndexer,
    SearchIndexerDataSourceConnection,
    SearchIndexerSkillset
)
from mlops.common.config_utils import MLOpsConfig


APPLICATION_JSON_CONTENT_TYPE = 'application/json'
CHUNKED_DATA_SOURCE_FILE_NAME = 'chunkedDataSource.json'
CHUNKED_INDEX_NAME = 'chunked'
CHUNKED_INDEX_FILE_NAME = 'chunkedIndex.json'
CHUNKED_INDEXER_FILE_NAME = 'chunkedIndexer.json'
DOCUMENT_DATA_SOURCE_FILE_NAME = 'documentDataSource.json'
DOCUMENT_INDEX_FILE_NAME = 'documentIndex.json'
DOCUMENT_INDEX_NAME = 'document'
DOCUMENT_INDEXER_FILE_NAME = 'documentIndexer.json'
DOCUMENT_INDEXER_NAME = 'document-indexer'
DOCUMENT_SKILLSET_FILE_NAME = 'documentSkillset.json'
ENV_FILE_NAME = '.env'
MANAGEMENT_SCOPE_URL = 'https://management.azure.com/.default'
RG_NAME = 'rg-playbook-rag'
ROOT_FILE_DIR = pathlib.Path(__file__).parent.resolve()
SEARCH_SVC_PREFIX = 'srch-playbook-rag'
STORAGE_ACCOUNT_PREFIX = 'stplaybookrag'
SUB_ID_ENV_VARIABLE_NAME = 'AZURE_SUBSCRIPTION_ID'


def _create_or_update_search_index(
        search_service_name: str,
        index_name: str,
        file_name: str,
        search_admin_key: str
) -> None:
    api_version = '2023-10-01-Preview'

    # Use the REST API, there is a bug in the Search SDK that prevents creating the Vector field correctly
    index_url = (
        "https://{service_name}.search.windows.net/indexes('{index_name}')"
    ).format(
        service_name=search_service_name,
        index_name=index_name
    )
    params = {
        'api-version': api_version,
        'allowIndexDowntime': 'true'
    }
    headers = {
        'Content-Type': APPLICATION_JSON_CONTENT_TYPE,
        'Accept': APPLICATION_JSON_CONTENT_TYPE,
        'Prefer': 'true',
        'api-key': search_admin_key

    }
    with open(ROOT_FILE_DIR / file_name) as index_file:
        index_def = index_file.read()

    response = requests.put(url=index_url, data=index_def, params=params, headers=headers)

    if response.status_code not in [200, 201, 204]:
        raise Exception(response.content)


def _get_storage_conn_string(credential: AzureCliCredential, sub_id: str) -> str:
    storage_client = StorageManagementClient(credential=credential, subscription_id=sub_id)
    storage_account_name = next(
        account for account in storage_client.storage_accounts.list() if account.name.startswith(STORAGE_ACCOUNT_PREFIX)
    ).name
    keys = storage_client.storage_accounts.list_keys(RG_NAME, storage_account_name)
    conn_string = (
        'DefaultEndpointsProtocol=https;AccountName={storage_account_name};' +
        'AccountKey={key};' +
        'EndpointSuffix=core.windows.net'
    ).format(
        storage_account_name=storage_account_name,
        key=keys.keys[0].value
    )

    return conn_string


def _generate_data_source_connection(file_name: str, conn_string: str):
    with open(ROOT_FILE_DIR / file_name) as data_source_file:
        data_source_def = data_source_file.read()

    data_source_def = data_source_def.replace('{conn_string}', conn_string)
    data_source_connection = SearchIndexerDataSourceConnection.deserialize(
        data_source_def,
        APPLICATION_JSON_CONTENT_TYPE
    )
    # I don't know why this is necessary, the connection string is in the credentials, it's not happy without it
    data_source_connection.connection_string = conn_string

    return data_source_connection


def _generate_skillset(credential: AzureCliCredential, conn_string: str, sub_id: str) -> SearchIndexerSkillset:
    # Get the function app name
    app_mgmt_client = WebSiteManagementClient(credential=credential, subscription_id=sub_id)
    # The function app uses a GUID function so the name is unknown before hand. There is only one function app in the RG
    rag_app = list(filter(lambda n: n.resource_group == RG_NAME, app_mgmt_client.web_apps.list()))[0]

    # Get the keys to each function
    clean_text_key = app_mgmt_client.web_apps.list_function_keys(
        resource_group_name=RG_NAME,
        name=rag_app.name,
        function_name='CleanText'
    ).additional_properties['default']
    key_phrase_key = app_mgmt_client.web_apps.list_function_keys(
        resource_group_name=RG_NAME,
        name=rag_app.name,
        function_name='KeyphraseExtraction'
    ).additional_properties['default']
    vector_key = app_mgmt_client.web_apps.list_function_keys(
        resource_group_name=RG_NAME,
        name=rag_app.name,
        function_name='VectorEmbeddingSkill'
    ).additional_properties['default']
    chunk_vector_key = app_mgmt_client.web_apps.list_function_keys(
        resource_group_name=RG_NAME,
        name=rag_app.name,
        function_name='ChunkVectorEmbedding'
    ).additional_properties['default']

    # Get the config
    with open(ROOT_FILE_DIR / DOCUMENT_SKILLSET_FILE_NAME) as skillset_file:
        skillset_def = skillset_file.read()

    # Get the AI Services Multi-Purpose Account Key
    ai_serv_mgmt_client = CognitiveServicesManagementClient(credential=credential, subscription_id=sub_id)
    ai_serv_account_key = ai_serv_mgmt_client.accounts.list_keys(
        resource_group_name=RG_NAME,
        account_name='ai-playbook-rag-multi'
    ).key1

    # Update the config
    skillset_def = skillset_def.replace('{function_app_name}', rag_app.name) \
        .replace('{clean_text_key}', clean_text_key) \
        .replace('{key_phrase_key}', key_phrase_key) \
        .replace('{vector_key}', vector_key) \
        .replace('{chunk_vector_key}', chunk_vector_key) \
        .replace('{ai_serv_account_key}', ai_serv_account_key) \
        .replace('{conn_string}', conn_string)

    skillset = SearchIndexerSkillset.deserialize(skillset_def, APPLICATION_JSON_CONTENT_TYPE)

    return skillset


def _generate_indexer(file_name: str, conn_string: str) -> SearchIndexer:
    with open(ROOT_FILE_DIR / file_name) as indexer_file:
        indexer_def = indexer_file.read()

    indexer_def = indexer_def.replace('{conn_string}', conn_string)

    indexer = SearchIndexer.deserialize(indexer_def, APPLICATION_JSON_CONTENT_TYPE)

    return indexer


def _wait_for_document_indexer(indexer_client: SearchIndexerClient):
    status = "Indexer {document_indexer_name} not started yet".format(document_indexer_name=DOCUMENT_INDEXER_NAME)

    while indexer_client.get_indexer_status(DOCUMENT_INDEXER_NAME).last_result is None or \
            (status := indexer_client.get_indexer_status(DOCUMENT_INDEXER_NAME).last_result.status) != 'success':
        print('Document indexer status: {status}'.format(status=status))

        if (status == 'transientFailure'):
            break

        time.sleep(10)


def main():
    credential = AzureCliCredential()
    search_management_client = SearchManagementClient(credential=credential, subscription_id=sub_id)
    search_service_name = next(
        service for service in search_management_client.services.list_by_resource_group(resource_group_name=RG_NAME)
        if service.name.startswith(SEARCH_SVC_PREFIX)
    ).name
    search_admin_key = search_management_client.admin_keys.get(
        resource_group_name=RG_NAME, search_service_name=search_service_name
    ).primary_key

    # Create the full document index
    _create_or_update_search_index(
        search_service_name=search_service_name,
        index_name=DOCUMENT_INDEX_NAME,
        file_name=DOCUMENT_INDEX_FILE_NAME,
        search_admin_key=search_admin_key
    )

    conn_string = _get_storage_conn_string(credential=credential, sub_id=sub_id)
    search_url = 'https://{search_svc_name}.search.windows.net'.format(search_svc_name=search_service_name)
    key_credential = AzureKeyCredential(search_admin_key)
    search_indexer_client = SearchIndexerClient(search_url, key_credential)

    # Create the full document Data Source for the Indexer
    document_data_source_connection = _generate_data_source_connection(
        file_name=DOCUMENT_DATA_SOURCE_FILE_NAME,
        conn_string=conn_string
    )
    search_indexer_client.create_or_update_data_source_connection(
        data_source_connection=document_data_source_connection
    )

    # Create full document Skillset
    document_skillset = _generate_skillset(credential=credential, conn_string=conn_string, sub_id=sub_id)
    search_indexer_client.create_or_update_skillset(skillset=document_skillset)

    # Create the full document Indexer
    document_indexer = _generate_indexer(file_name=DOCUMENT_INDEXER_FILE_NAME, conn_string=conn_string)
    search_indexer_client.create_or_update_indexer(indexer=document_indexer)

    # Wait for the full document indexer to complete so that the chunked indexer can execute on results
    _wait_for_document_indexer(search_indexer_client)

    # Create the chunked index
    _create_or_update_search_index(
        search_service_name=search_service_name,
        index_name=CHUNKED_INDEX_NAME,
        file_name=CHUNKED_INDEX_FILE_NAME,
        search_admin_key=search_admin_key
    )

    # Create the chunked Data Source for the Indexer
    chunked_data_source_connection = _generate_data_source_connection(
        file_name=CHUNKED_DATA_SOURCE_FILE_NAME,
        conn_string=conn_string
    )
    search_indexer_client.create_or_update_data_source_connection(
        data_source_connection=chunked_data_source_connection
    )

    # Create the chunked Indexer
    chunked_indexer = _generate_indexer(file_name=CHUNKED_INDEXER_FILE_NAME, conn_string=conn_string)
    search_indexer_client.create_or_update_indexer(indexer=chunked_indexer)


if __name__ == "__main__":
    main()