"""Performs cleanup of PRs that are closed and merged."""

from mlops.common.config_utils import MLOpsConfig
from mlops.common.naming_utils import generate_slot_name
from azure.identity import DefaultAzureCredential
from azure.mgmt.web import WebSiteManagementClient


def main():
    """Delete a function slot when the PR is merged."""
    print("Cleanup PRs")
    config = MLOpsConfig()

    # subscription config section in yaml
    subscription_id = config.sub_config["subscription_id"]
    resource_group = config.sub_config["resource_group_name"]

    # functions_config contains a section with function settings
    function_app_name = config.functions_config["function_app_name"]

    slot_name = generate_slot_name()
    credential = DefaultAzureCredential()
    web_client = WebSiteManagementClient(credential, subscription_id)
    web_client.web_apps.delete_slot(resource_group, function_app_name, slot_name)


if __name__ == "__main__":
    main()
