"""Agent for chatting with documents indexed in Azure AI Search."""

import asyncio
import argparse

from azure.identity.aio import DefaultAzureCredential
from azure.ai.agents.models import AzureAISearchTool, AzureAISearchQueryType
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.agents import AzureAIAgentThread


AGENT_NAME = "DocumentChatAgent"
AGENT_INSTRUCTIONS = (
    "You are a helpful assistant that answers questions about documents "
    "stored in an Azure AI Search index. Use the search tool to find relevant "
    "information and provide accurate, concise answers based on the indexed content. "
    "If the answer is not found in the indexed documents, say so clearly."
)


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
    """Run the document chat agent locally using command-line arguments or environment variables."""
    parser = argparse.ArgumentParser(
        description="Run an interactive chat session with indexed documents."
    )
    parser.add_argument(
        "--connection-id",
        required=True,
        help="Azure AI Foundry connection ID for the Azure AI Search service.",
    )
    parser.add_argument(
        "--index-name",
        required=True,
        help="Name of the Azure AI Search index to query.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "Model deployment name. Defaults to AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME "
            "environment variable if not specified."
        ),
    )
    parser.add_argument(
        "--endpoint",
        default=None,
        help=(
            "Azure AI Foundry project endpoint. Defaults to AZURE_AI_AGENT_ENDPOINT "
            "environment variable if not specified."
        ),
    )
    args = parser.parse_args()

    settings = AzureAIAgentSettings()
    model = args.model or settings.model_deployment_name
    endpoint = args.endpoint or settings.endpoint

    asyncio.run(
        run_local_chat(
            ai_search_connection_id=args.connection_id,
            ai_search_index_name=args.index_name,
            model_deployment_name=model,
            endpoint=endpoint,
        )
    )


if __name__ == "__main__":
    main()
