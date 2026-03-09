"""Agent for chatting with documents indexed in Azure AI Search."""

import asyncio

from azure.identity import DefaultAzureCredential as SyncDefaultAzureCredential
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects import AIProjectClient as SyncAIProjectClient
from azure.ai.projects.models import ConnectionType
from azure.ai.agents.models import AzureAISearchTool, AzureAISearchQueryType
from azure.ai.ml import MLClient
from azure.ai.ml.entities import AzureAISearchConnection
from semantic_kernel.agents import AzureAIAgent
from semantic_kernel.agents import AzureAIAgentThread

from mlops.common.config_utils import MLOpsConfig
from mlops.common.naming_utils import generate_index_name


AGENT_NAME = "DocumentChatAgent"
AGENT_INSTRUCTIONS = (
    "You are a helpful assistant that answers questions about documents "
    "stored in an Azure AI Search index. Use the search tool to find relevant "
    "information and provide accurate, concise answers based on the indexed content. "
    "If the answer is not found in the indexed documents, say so clearly."
)


def _extract_project_name(endpoint: str) -> str:
    """
    Extract the AI Foundry project name from the project endpoint URL.

    Args:
        endpoint (str): URL in the form
            ``https://<hub>.services.ai.azure.com/api/projects/<project>``.

    Returns:
        str: The project name (last path segment of the URL).
    """
    return endpoint.rstrip("/").split("/")[-1]


def ensure_ai_search_connection_id(
    endpoint: str,
    acs_service_name: str,
    subscription_id: str,
    resource_group_name: str,
) -> str:
    """
    Return the AI Foundry connection ID for the given Azure AI Search service,
    creating the connection if it does not already exist.

    First checks whether a connection whose target URL contains
    ``acs_service_name`` is already registered in the project.  If no such
    connection exists, one is created via the Azure AI ML management SDK using
    AAD/managed-identity authentication (no API key required).

    Args:
        endpoint (str): The Azure AI Foundry project endpoint.
        acs_service_name (str): The Azure AI Search service name (e.g. 'my-search').
        subscription_id (str): Azure subscription ID.
        resource_group_name (str): Azure resource group name.

    Returns:
        str: The connection ID to use with the AI Search tool.
    """
    credential = SyncDefaultAzureCredential()
    client = SyncAIProjectClient(endpoint=endpoint, credential=credential)
    connections = list(client.connections.list(connection_type=ConnectionType.AZURE_AI_SEARCH))

    # Return the connection whose target URL matches the configured service name
    matched = next(
        (c for c in connections if acs_service_name.lower() in c.target.lower()),
        None,
    )
    if matched:
        return matched.id

    # No matching connection found — create one using the management SDK
    print(
        f"No AI Search connection found for '{acs_service_name}'. "
        "Creating connection in AI Foundry..."
    )
    project_name = _extract_project_name(endpoint)
    ml_client = MLClient(
        credential=credential,
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        workspace_name=project_name,
    )
    new_connection = AzureAISearchConnection(
        name=acs_service_name,
        endpoint=f"https://{acs_service_name}.search.windows.net",
    )
    created = ml_client.connections.create_or_update(new_connection)
    return created.id


async def create_agent(
    ai_search_connection_id: str,
    ai_search_index_name: str,
    model_deployment_name: str,
    endpoint: str,
) -> AzureAIAgent:
    """
    Create an AzureAIAgent configured with an Azure AI Search tool.

    Args:
        ai_search_connection_id (str): The AI Foundry connection ID for Azure AI Search.
        ai_search_index_name (str): The name of the Azure AI Search index to query.
        model_deployment_name (str): The model deployment name to use for the agent.
        endpoint (str): The Azure AI Foundry project endpoint.

    Returns:
        AzureAIAgent: Configured agent instance.
    """
    ai_search_tool = AzureAISearchTool(
        index_connection_id=ai_search_connection_id,
        index_name=ai_search_index_name,
        query_type=AzureAISearchQueryType.VECTOR_SEMANTIC_HYBRID,
        top_k=5,
    )

    credential = DefaultAzureCredential()
    client = AzureAIAgent.create_client(credential=credential, endpoint=endpoint)
    agent_definition = await client.agents.create_agent(
        model=model_deployment_name,
        name=AGENT_NAME,
        instructions=AGENT_INSTRUCTIONS,
        tools=ai_search_tool.definitions,
        tool_resources=ai_search_tool.resources,
    )

    return AzureAIAgent(client=client, definition=agent_definition)


async def run_agent_conversation(agent: AzureAIAgent, user_message: str) -> str:
    """
    Send a single message to the agent and return the response.

    Args:
        agent (AzureAIAgent): The configured agent instance.
        user_message (str): The user's query message.

    Returns:
        str: The agent's response text.
    """
    thread: AzureAIAgentThread | None = None
    try:
        thread = AzureAIAgentThread(client=agent.client)
        response_parts = []
        async for response in agent.invoke(
            messages=user_message,
            thread=thread,
        ):
            response_parts.append(str(response.content))
        return "".join(response_parts)
    finally:
        if thread is not None:
            await thread.delete()


async def run_local_chat(
    ai_search_connection_id: str,
    ai_search_index_name: str,
    model_deployment_name: str,
    endpoint: str,
) -> None:
    """
    Run an interactive local chat session with the document agent.

    Args:
        ai_search_connection_id (str): The AI Foundry connection ID for Azure AI Search.
        ai_search_index_name (str): The name of the Azure AI Search index to query.
        model_deployment_name (str): The model deployment name to use for the agent.
        endpoint (str): The Azure AI Foundry project endpoint.
    """
    print("Initializing Document Chat Agent...")
    agent = await create_agent(
        ai_search_connection_id=ai_search_connection_id,
        ai_search_index_name=ai_search_index_name,
        model_deployment_name=model_deployment_name,
        endpoint=endpoint,
    )
    print(f"Agent '{AGENT_NAME}' is ready. Type 'exit' or 'quit' to stop.\n")

    try:
        while True:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                print("Goodbye!")
                break
            response = await run_agent_conversation(agent, user_input)
            print(f"Agent: {response}\n")
    finally:
        await agent.client.agents.delete_agent(agent.id)


def main():
    """Run the document chat agent locally using configuration from config.yaml."""
    config = MLOpsConfig()
    agent_config = config.agent_config
    acs_config = config.acs_config
    sub_config = config.sub_config

    endpoint = agent_config["agent_endpoint"]
    model = agent_config["agent_model_deployment"]
    acs_service_name = acs_config["acs_service_name"]
    subscription_id = sub_config["subscription_id"]
    resource_group_name = sub_config["resource_group_name"]
    index_name = generate_index_name()

    print(f"Looking up AI Search connection for service '{acs_service_name}'...")
    connection_id = ensure_ai_search_connection_id(
        endpoint=endpoint,
        acs_service_name=acs_service_name,
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
    )

    asyncio.run(
        run_local_chat(
            ai_search_connection_id=connection_id,
            ai_search_index_name=index_name,
            model_deployment_name=model,
            endpoint=endpoint,
        )
    )


if __name__ == "__main__":
    main()
