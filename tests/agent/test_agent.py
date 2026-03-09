"""Unit tests for the document chat agent."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from azure.ai.projects.models import ConnectionType


class TestGetAISearchConnectionId(unittest.TestCase):
    """Tests for the get_ai_search_connection_id function."""

    @patch("src.agent.agent.SyncAIProjectClient")
    @patch("src.agent.agent.SyncDefaultAzureCredential")
    def test_returns_matching_connection_by_service_name(
        self, mock_cred_cls, mock_client_cls
    ):
        """Test that the connection whose target contains acs_service_name is returned."""
        from src.agent.agent import get_ai_search_connection_id

        conn1 = MagicMock()
        conn1.id = "/connections/other-search"
        conn1.target = "https://other-search.search.windows.net"
        conn1.is_default = False

        conn2 = MagicMock()
        conn2.id = "/connections/my-search"
        conn2.target = "https://my-search.search.windows.net"
        conn2.is_default = False

        mock_client = MagicMock()
        mock_client.connections.list.return_value = [conn1, conn2]
        mock_client_cls.return_value = mock_client

        result = get_ai_search_connection_id(
            endpoint="https://test.services.ai.azure.com/api/projects/p",
            acs_service_name="my-search",
        )

        self.assertEqual(result, "/connections/my-search")
        mock_client.connections.list.assert_called_once_with(
            connection_type=ConnectionType.AZURE_AI_SEARCH
        )

    @patch("src.agent.agent.SyncAIProjectClient")
    @patch("src.agent.agent.SyncDefaultAzureCredential")
    def test_falls_back_to_default_when_no_name_match(
        self, mock_cred_cls, mock_client_cls
    ):
        """Test fallback to default connection when service name has no match."""
        from src.agent.agent import get_ai_search_connection_id

        conn1 = MagicMock()
        conn1.id = "/connections/first"
        conn1.target = "https://first.search.windows.net"
        conn1.is_default = False

        conn2 = MagicMock()
        conn2.id = "/connections/default"
        conn2.target = "https://default.search.windows.net"
        conn2.is_default = True

        mock_client = MagicMock()
        mock_client.connections.list.return_value = [conn1, conn2]
        mock_client_cls.return_value = mock_client

        result = get_ai_search_connection_id(
            endpoint="https://test.services.ai.azure.com/api/projects/p",
            acs_service_name="no-match-here",
        )

        self.assertEqual(result, "/connections/default")

    @patch("src.agent.agent.SyncAIProjectClient")
    @patch("src.agent.agent.SyncDefaultAzureCredential")
    def test_raises_when_no_connections_found(self, mock_cred_cls, mock_client_cls):
        """Test that ValueError is raised when no AI Search connections exist."""
        from src.agent.agent import get_ai_search_connection_id

        mock_client = MagicMock()
        mock_client.connections.list.return_value = []
        mock_client_cls.return_value = mock_client

        with self.assertRaises(ValueError):
            get_ai_search_connection_id(
                endpoint="https://test.services.ai.azure.com/api/projects/p",
                acs_service_name="my-search",
            )


class TestCreateAgent(unittest.IsolatedAsyncioTestCase):
    """Tests for the create_agent function."""

    @patch("src.agent.agent.AzureAIAgent")
    @patch("src.agent.agent.DefaultAzureCredential")
    async def test_create_agent_builds_correct_tool(
        self, mock_credential_cls, mock_agent_cls
    ):
        """Test that create_agent configures the AI Search tool correctly."""
        from src.agent.agent import create_agent, AGENT_NAME, AGENT_INSTRUCTIONS

        mock_credential = AsyncMock()
        mock_credential_cls.return_value = mock_credential

        mock_client = MagicMock()
        mock_agent_cls.create_client.return_value = mock_client

        mock_agent_definition = MagicMock()
        mock_agent_definition.name = AGENT_NAME
        mock_agent_definition.id = "agent-123"
        mock_agent_definition.description = None
        mock_agent_definition.instructions = AGENT_INSTRUCTIONS
        mock_client.agents.create_agent = AsyncMock(return_value=mock_agent_definition)

        mock_agent = MagicMock()
        mock_agent_cls.return_value = mock_agent

        agent = await create_agent(
            ai_search_connection_id="test-connection-id",
            ai_search_index_name="test-index",
            model_deployment_name="gpt-4o",
            endpoint="https://test.services.ai.azure.com/api/projects/test-project",
        )

        mock_client.agents.create_agent.assert_awaited_once()
        call_kwargs = mock_client.agents.create_agent.call_args.kwargs
        self.assertEqual(call_kwargs["model"], "gpt-4o")
        self.assertEqual(call_kwargs["name"], AGENT_NAME)
        self.assertEqual(call_kwargs["instructions"], AGENT_INSTRUCTIONS)
        self.assertIsNotNone(call_kwargs["tools"])
        self.assertIsNotNone(call_kwargs["tool_resources"])

        self.assertEqual(agent, mock_agent)

    @patch("src.agent.agent.AzureAIAgent")
    @patch("src.agent.agent.DefaultAzureCredential")
    async def test_create_agent_uses_provided_endpoint(
        self, mock_credential_cls, mock_agent_cls
    ):
        """Test that create_agent passes the provided endpoint to create_client."""
        from src.agent.agent import create_agent, AGENT_INSTRUCTIONS, AGENT_NAME

        expected_endpoint = "https://my-project.services.ai.azure.com/api/projects/proj"
        mock_credential = AsyncMock()
        mock_credential_cls.return_value = mock_credential

        mock_client = MagicMock()
        mock_agent_cls.create_client.return_value = mock_client

        mock_agent_definition = MagicMock()
        mock_agent_definition.name = AGENT_NAME
        mock_agent_definition.id = "agent-456"
        mock_agent_definition.description = None
        mock_agent_definition.instructions = AGENT_INSTRUCTIONS
        mock_client.agents.create_agent = AsyncMock(return_value=mock_agent_definition)

        mock_agent_cls.return_value = MagicMock()

        await create_agent(
            ai_search_connection_id="conn-id",
            ai_search_index_name="idx",
            model_deployment_name="gpt-4o",
            endpoint=expected_endpoint,
        )

        mock_agent_cls.create_client.assert_called_once_with(
            credential=mock_credential, endpoint=expected_endpoint
        )


class TestRunAgentConversation(unittest.IsolatedAsyncioTestCase):
    """Tests for the run_agent_conversation function."""

    @patch("src.agent.agent.AzureAIAgentThread")
    async def test_run_agent_conversation_returns_response(self, mock_thread_cls):
        """Test that run_agent_conversation returns the agent response text."""
        from src.agent.agent import run_agent_conversation

        mock_thread = MagicMock()
        mock_thread.delete = AsyncMock()
        mock_thread_cls.return_value = mock_thread

        mock_response = MagicMock()
        mock_response.content = "This is the answer from indexed documents."

        async def fake_invoke(**kwargs):
            yield mock_response

        mock_agent = MagicMock()
        mock_agent.invoke = fake_invoke
        mock_agent.client = MagicMock()

        result = await run_agent_conversation(mock_agent, "What is this document about?")

        self.assertEqual(result, "This is the answer from indexed documents.")
        mock_thread.delete.assert_awaited_once()

    @patch("src.agent.agent.AzureAIAgentThread")
    async def test_run_agent_conversation_deletes_thread_on_error(self, mock_thread_cls):
        """Test that run_agent_conversation cleans up thread even when an error occurs."""
        from src.agent.agent import run_agent_conversation

        mock_thread = MagicMock()
        mock_thread.delete = AsyncMock()
        mock_thread_cls.return_value = mock_thread

        async def failing_invoke(**kwargs):
            if False:
                yield
            raise RuntimeError("Search failed")

        mock_agent = MagicMock()
        mock_agent.invoke = failing_invoke
        mock_agent.client = MagicMock()

        with self.assertRaises(RuntimeError):
            await run_agent_conversation(mock_agent, "What is this document about?")

        mock_thread.delete.assert_awaited_once()

    @patch("src.agent.agent.AzureAIAgentThread")
    async def test_run_agent_conversation_concatenates_multiple_responses(
        self, mock_thread_cls
    ):
        """Test that multiple response chunks are concatenated."""
        from src.agent.agent import run_agent_conversation

        mock_thread = MagicMock()
        mock_thread.delete = AsyncMock()
        mock_thread_cls.return_value = mock_thread

        mock_resp1 = MagicMock()
        mock_resp1.content = "Part one. "
        mock_resp2 = MagicMock()
        mock_resp2.content = "Part two."

        async def multi_invoke(**kwargs):
            yield mock_resp1
            yield mock_resp2

        mock_agent = MagicMock()
        mock_agent.invoke = multi_invoke
        mock_agent.client = MagicMock()

        result = await run_agent_conversation(mock_agent, "Tell me more.")

        self.assertEqual(result, "Part one. Part two.")
        mock_thread.delete.assert_awaited_once()


class TestAgentConstants(unittest.TestCase):
    """Tests for agent module constants and defaults."""

    def test_agent_name_is_defined(self):
        """Test that AGENT_NAME constant is defined."""
        from src.agent.agent import AGENT_NAME

        self.assertIsInstance(AGENT_NAME, str)
        self.assertTrue(len(AGENT_NAME) > 0)

    def test_agent_instructions_mention_search(self):
        """Test that AGENT_INSTRUCTIONS reference AI Search usage."""
        from src.agent.agent import AGENT_INSTRUCTIONS

        self.assertIsInstance(AGENT_INSTRUCTIONS, str)
        self.assertIn("search", AGENT_INSTRUCTIONS.lower())
