"""This module contains a few utility methods that allow us to verify functions work as expected."""


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
