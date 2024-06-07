"""Performs cleanup of PRs that are closed and merged."""

import requests
from mlops.common.config_utils import MLOpsConfig
from mlops.common.naming_utils import (generate_index_name,
                                       generate_indexer_name,
                                       generate_data_source_name,
                                       generate_skillset_name,
                                       generate_slot_name
                                       )
from azure.identity import DefaultAzureCredential
from azure.mgmt.web import WebSiteManagementClient
from azure.core.exceptions import ResourceNotFoundError


def delete_function_app_slot(config: MLOpsConfig):
    """Delete a function slot when the PR is merged."""
    # subscription config section in yaml
    subscription_id = config.sub_config["subscription_id"]
    resource_group_name = config.sub_config["resource_group_name"]

    # functions_config contains a section with function settings
    function_app_name = config.functions_config["function_app_name"]
    slot_name = generate_slot_name()
    credential = DefaultAzureCredential()
    web_client = WebSiteManagementClient(credential, subscription_id)

    try:
        # Try to get the slot to check if it exists
        _ = web_client.web_apps.get_slot(resource_group_name, function_app_name, slot_name)
        print(f"Slot '{slot_name}' exists. Deleting...")

        # Delete the slot if it exists
        web_client.web_apps.delete_slot(resource_group_name, function_app_name, slot_name)
        print(f"Slot '{slot_name}' deleted successfully.")
    except ResourceNotFoundError:
        # If the slot does not exist, an exception is thrown
        print(f"Slot '{slot_name}' does not exist. No action needed.")


def delete_indexer_entity(config: MLOpsConfig, entity_name: str, entity_type: str):
    """Delete indexer entity."""
    # Get the variables
    endpoint = config.acs_config["acs_api_base"]
    api_version = config.acs_config["acs_api_version"]
    admin_api_key = config.acs_config["acs_api_key"]

    # Construct the request URL
    url = f"{endpoint}/{entity_type}/{entity_name}?api-version={api_version}"

    # Set the headers
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_api_key
    }

    # Make the DELETE request
    response = requests.delete(url, headers=headers)

    # Check the response
    if response.status_code == 204:
        print(f"{entity_type} '{entity_name}' has been successfully deleted.")
    else:
        print(f"Failed to delete {entity_type} '{entity_name}'.")
        print(f"Status code: {response.status_code}, Response: {response.text}")


def delete_indexer_entities(config: MLOpsConfig):
    """Delete indexer entities when the PR is merged."""
    delete_indexer_entity(config, generate_index_name(), "indexes")
    delete_indexer_entity(config, generate_skillset_name(), "skillsets")
    delete_indexer_entity(config, generate_data_source_name(), "datasources")
    delete_indexer_entity(config, generate_indexer_name(), "indexers")


def main():
    """Cleanup PR artifacts."""
    print("Cleanup PRs")
    config = MLOpsConfig()

    delete_function_app_slot(config)
    delete_indexer_entities(config)


if __name__ == "__main__":
    main()
