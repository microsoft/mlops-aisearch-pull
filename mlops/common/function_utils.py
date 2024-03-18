"""This module contains a few utility methods that allow us to verify functions work as expected."""
from azure.identity import DefaultAzureCredential
from azure.mgmt.web import WebSiteManagementClient


def get_app_settings(config: dict, index_name: str):
    """Get the function app settings."""
    settings_dict = {}
    settings_dict["AZURE_OPENAI_API_KEY"] = config.aoai_config["aoai_api_key"]
    settings_dict["AZURE_OPENAI_API_VERSION"] = config.aoai_config["aoai_api_version"]
    settings_dict["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"] = config.aoai_config["aoai_embedding_model_deployment"]
    settings_dict["AZURE_OPENAI_ENDPOINT"] = config.aoai_config["aoai_api_base"]
    settings_dict["AZURE_SEARCH_ENDPOINT"] = config.acs_config["acs_api_base"]

    settings_dict["AZURE_SEARCH_API_KEY"] = config.acs_config["acs_api_key"]
    settings_dict["AZURE_SEARCH_API_VERSION"] = config.acs_config["acs_api_version"]
    settings_dict["AZURE_SEARCH_INDEX_NAME"] = index_name
    settings_dict["AZURE_STORAGE_ACCOUNT_CONNECTION_STRING"] = config.sub_config["storage_account_connection_string"]
    settings_dict["AZURE_STORAGE_CONTAINER_NAME"] = config.get_flow_config("data")["storage_container"]

    settings_dict["ENABLE_ORYX_BUILD"] = "true"
    settings_dict["SCM_DO_BUILD_DURING_DEPLOYMENT"] = "true"
    return settings_dict

def get_function_key(
    credential: DefaultAzureCredential,
    subscription_id: str,
    resource_group_name: str,
    function_app_name: str,
    function_name: str,
    slot: str | None,
) -> str:
    """Get the function key."""
    # This is a temporary solution to get the function key
    # This should be replaced with a proper way to get the function key
    # for the given function
    app_mgmt_client = WebSiteManagementClient(
        credential=credential, subscription_id=subscription_id
    )
    # get the function key
    if slot is None:
        function_key = app_mgmt_client.web_apps.list_function_keys(
            resource_group_name, function_app_name, function_name
        )
    else:
        function_key = app_mgmt_client.web_apps.list_function_keys_slot(
            resource_group_name, function_app_name, function_name, slot
        )
    result = function_key.additional_properties["default"]
    return result
