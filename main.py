"""Main entry point."""

from dotenv import load_dotenv

# from mlops.deployment_scripts.build_indexer import main as build_indexer_main
from mlops.deployment_scripts.run_functions import main as run_functions_main

load_dotenv()
# from mlops.deployment_scripts.deploy_azure_functions import (
#     main as deploy_azure_functions_main,
# )


if __name__ == "__main__":
    # deploy_azure_functions_main()
    run_functions_main()
