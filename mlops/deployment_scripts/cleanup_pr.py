"""Performs cleanup of PRs that are closed and merged."""

from mlops.common.config_utils import MLOpsConfig
from mlops.common.naming_utils import generate_slot_name
from azure.identity import DefaultAzureCredential
from azure.mgmt.web import WebSiteManagementClient
from azure.core.exceptions import ResourceNotFoundError


def main():
    """Delete a function slot when the PR is merged."""
    print("Cleanup PRs")
    config = MLOpsConfig()

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


if __name__ == "__main__":
    main()
