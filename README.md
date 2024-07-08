# MLOps Template for Azure AI Search: Pull approach

This repository demonstrates how to implement a Machine Learning Development and Operations (MLOps) process for [Azure AI Search](https://learn.microsoft.com/en-us/azure/search/) applications that use a [pull model](https://learn.microsoft.com/en-us/azure/search/search-what-is-data-import#pulling-data-into-an-index) to index data. It creates an indexer with two custom skills that pull pdf documents from a blob storage container, chunks them, creates embeddings for the chunks and then adds the chunks into an index. Finally, it performs search evaluation for a collection of data and uploads the results to an [AI Studio](https://learn.microsoft.com/en-us/azure/ai-studio/) project so that evaluations can be compared across multiple runs to continue improving the custom skills.

## Technical Requirements

- [Azure AI Search](https://learn.microsoft.com/en-us/azure/search/)
- [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/overview)
- [Azure AI Studio](https://learn.microsoft.com/en-us/azure/ai-studio/) project
- [Azure Function App](https://learn.microsoft.com/en-us/azure/azure-functions/)
  - For the best performance of the skillset functions and slot deployments, it is recommended to use an App Service Plan with a level of at least `Standard S3`
- Azure Storage Account

## Folder Structure

Below are some key folders within the project:

- **src/custom_skills**: Contains the function app which has the chunking and embedding skillset functions used by the indexer
- **mlops**: Contains the scripts for implmenting MLOPs flows
- **config**: Configuration for the MLOPs scripts
- **data**: Sample data for testing the indexer
- **.github**: GitHub workflows that can be used to run an MLOPs pipeline
- **.devcontainer**: Contains a development container that can help you work with the repo and develop Azure functions

Additionally, the root folder contains some important files:

- **.env.sample**: The file should be renamed to `.env` and sensitive parameters (parameters that cannot be hardcodeded in `config.yaml`) should be populated here.
- **setup.cfg**: The repo uses strict rules to validate code quality using flake8. This file contains applied rules and exceptions.
- **requirements.txt**: This file lists all the packages that the repo is using.

## Local Execution

The deployment scripts and github workflows use the git branch name to create a unique naming scheme for all of the deployed entities.

### Configuration

- Create an `.env` file based on `.env.sample` and populate the appropriate values.
- Modify `config/config.yaml` to meet any changes that have been made within the project.

### Upload test data

Sample pdfs are available in `data` to use for indexer testing.  To upload the data to blob storage, use the following:

```sh
python -m mlops.deployment_scripts.upload_data
```

### Deploy Skillset Functions

The following deployment script will deploy the custom skillset functions to a function app deployment slot and poll the functions until they are ready to be tested:

```sh
python -m mlops.deployment_scripts.deploy_azure_functions
```

To test the two skillset functions after they are deployed, run the following script:

```sh
python -m mlops.deployment_scripts.run_functions
```

More information aboud local development of skillset functions can be found in the [custom skills readme](./src/custom_skills/readme.md).

### Deploy Indexer

An indexer is composed for four entities: index, datasource, skillset, and indexer.  The configuration for each is defined by the files in `mlops/acs_config`. To deploy the indexer and commence indexing the data in blob storage, run the following:

```sh
python -m mlops.deployment_scripts.build_indexer
```

### Perform Search Evaluation

This will perform search evaluation and upload the result to the AI Studio project specified. For more information about evaluation, see the [search evaluation readme](/mlops/evaluation/readme.md).

```sh
python -m mlops.evaluation.search_evaluation --gt_path "./mlops/evaluation/data/search_evaluation_data.jsonl" --semantic_config my-semantic-config`
```

### Cleanup Deployment

Since the git branch name was used to create the deployed entities, this deployment script will clean up everything by deleting the deployment slot in the function app and the indexer entities.

```sh
python -m mlops.deployment_scripts.cleanup_pr
```

## DevOps Pipelines

This project contains github workflows for PR validation and Continuous Integration (CI).

The PR workflow executes quality checks using flake8 and unit tests. It then deploys the skillset functions to a deployment slot of the function app.  Once the functions are deployed and tested, an indexer is deployed and all of the test data is ingested from blob storage.  Search evaluation is run and uploaded to an AI Studio project.

The CI workflow executes a similar workflow to the PR workflow, but the skillset functions are deployed to the main function app, not a deployment slot.

In order for the cleanup step of the CI Workflow to work correctly, the development branch from a pull request must not be deleted until the cleanup step has run.

Some variables and secrets should be provided to execute the github workflows (primarily the same ones used in the `.env` file for local execution).

- azure_credentials
- subscription_id
- resource_group_name
- storage_account_name
- acs_service_name
- acs_api_key
- aoai_base_endpoint
- aoai_api_key
- storage_account_connection_string
- ai_studio_project_name

## Related Projects

- [mlops-promptflow-prompt](https://github.com/microsoft/mlops-promptflow-prompt) - This repository demonstrates how AI Studio and Prompt flow can be utilized in the Machine Learning Development and Operations (MLOps) process for LLM-based applications (aka LLMOps). It has base examples for inference evaluation using Prompt flow. When combined with [mlops-aisearch-pull](/README.md) for search evaluation, a full end-to-end MLOPs workflow can be achieved.

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit <https://cla.opensource.microsoft.com>.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
