"""
Test cases for agent functionality in the unicef-geospatial application.
"""

import os
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml
from llama_index.core.agent.workflow import AgentStream

from unicef_geospatial.agent.agent import create_agent, get_llm, run_agent


class TestGetLLM:
    """Test cases for the get_llm function."""

    @patch.dict(
        os.environ,
        {
            "MODEL_NAME": "gpt-4o-mini",
            "OPENAI_API_KEY": "test-key",
            "LANGFUSE_PROJECT_ID": "test-project",
        },
    )
    @patch("unicef_geospatial.agent.agent.LiteLLM")
    def test_get_llm_with_default_model(self, mock_litellm):
        """Test get_llm function with default model configuration."""
        mock_instance = MagicMock()
        mock_litellm.return_value = mock_instance

        temperature = 0.5
        session_id = "test-session-123"
        trace_id = "test-trace-456"

        result = get_llm(temperature, session_id, trace_id)

        mock_litellm.assert_called_once_with(
            model="gpt-4o-mini",
            temperature=temperature,
            openai_api_key="test-key",
            model_kwargs={
                "metadata": {
                    "session_id": session_id,
                    "project_id": "test-project",
                    "trace_id": trace_id,
                }
            },
        )
        assert result == mock_instance

    @patch.dict(
        os.environ,
        {
            "MODEL_NAME": "gpt-4",
            "OPENAI_API_KEY": "custom-key",
            "LANGFUSE_PROJECT_ID": "custom-project",
        },
    )
    @patch("unicef_geospatial.agent.agent.LiteLLM")
    def test_get_llm_with_custom_model(self, mock_litellm):
        """Test get_llm function with custom model configuration."""
        mock_instance = MagicMock()
        mock_litellm.return_value = mock_instance

        temperature = 0.7
        session_id = "custom-session"
        trace_id = "custom-trace"

        result = get_llm(temperature, session_id, trace_id)

        mock_litellm.assert_called_once_with(
            model="gpt-4",
            temperature=temperature,
            openai_api_key="custom-key",
            model_kwargs={
                "metadata": {
                    "session_id": session_id,
                    "project_id": "custom-project",
                    "trace_id": trace_id,
                }
            },
        )
        assert result == mock_instance

    @patch.dict(os.environ, {}, clear=True)
    @patch("unicef_geospatial.agent.agent.LiteLLM")
    def test_get_llm_with_missing_env_vars(self, mock_litellm):
        """Test get_llm function with missing environment variables."""
        mock_instance = MagicMock()
        mock_litellm.return_value = mock_instance

        temperature = 0.3
        session_id = "test-session"
        trace_id = "test-trace"

        result = get_llm(temperature, session_id, trace_id)

        mock_litellm.assert_called_once_with(
            model="gpt-4o-mini",
            temperature=temperature,
            openai_api_key=None,
            model_kwargs={
                "metadata": {
                    "session_id": session_id,
                    "project_id": None,
                    "trace_id": trace_id,
                }
            },
        )
        assert result == mock_instance


class TestCreateAgent:
    """Test cases for the create_agent function."""

    @pytest.fixture
    def mock_prompts(self):
        """Mock prompts loaded from YAML file."""
        return yaml.safe_load(open("unicef_geospatial/utils/prompts.yaml"))

    @patch("unicef_geospatial.agent.agent.get_llm")
    @patch("unicef_geospatial.agent.agent.ReActAgent")
    @patch("builtins.open", new_callable=mock_open)
    @patch("unicef_geospatial.agent.agent.yaml.safe_load")
    def test_create_agent_with_default_parameters(
        self, mock_yaml_load, mock_file, mock_react_agent, mock_get_llm, mock_prompts
    ):
        """Test create_agent function with default parameters."""
        mock_yaml_load.return_value = mock_prompts
        mock_llm_instance = MagicMock()
        mock_get_llm.return_value = mock_llm_instance
        mock_agent_instance = MagicMock()
        mock_react_agent.return_value = mock_agent_instance

        session_id = "test-session"
        trace_id = "test-trace"

        result = create_agent(session_id, trace_id)

        mock_get_llm.assert_called_once_with(0.0, session_id, trace_id)
        mock_react_agent.assert_called_once_with(
            tools=None,
            llm=mock_llm_instance,
            system_prompt=mock_prompts["system_prompt"],
        )
        mock_agent_instance.update_prompts.assert_called_once_with(
            {
                "react_header": mock_prompts["header_prompt"],
            }
        )
        assert result == mock_agent_instance

    @patch("unicef_geospatial.agent.agent.get_llm")
    @patch("unicef_geospatial.agent.agent.ReActAgent")
    @patch("unicef_geospatial.agent.agent.yaml.safe_load")
    def test_create_agent_with_custom_parameters(
        self, mock_yaml_load, mock_react_agent, mock_get_llm, mock_prompts
    ):
        """Test create_agent function with custom parameters."""
        mock_yaml_load.return_value = mock_prompts
        mock_llm_instance = MagicMock()
        mock_get_llm.return_value = mock_llm_instance
        mock_agent_instance = MagicMock()
        mock_react_agent.return_value = mock_agent_instance

        session_id = "custom-session"
        trace_id = "custom-trace"
        temperature = 0.8
        mock_tools = [MagicMock(), MagicMock()]
        custom_system_prompt = "Custom system prompt"

        result = create_agent(
            session_id=session_id,
            trace_id=trace_id,
            temperature=temperature,
            tools=mock_tools,
            system_prompt=custom_system_prompt,
        )

        mock_get_llm.assert_called_once_with(temperature, session_id, trace_id)
        mock_react_agent.assert_called_once_with(
            tools=mock_tools,
            llm=mock_llm_instance,
            system_prompt=custom_system_prompt,
        )
        mock_agent_instance.update_prompts.assert_called_once_with(
            {
                "react_header": mock_prompts["header_prompt"],
            }
        )
        assert result == mock_agent_instance

    @patch("unicef_geospatial.agent.agent.get_llm")
    @patch("unicef_geospatial.agent.agent.ReActAgent")
    @patch("unicef_geospatial.agent.agent.yaml.safe_load")
    def test_create_agent_with_empty_tools_list(
        self, mock_yaml_load, mock_react_agent, mock_get_llm, mock_prompts
    ):
        """Test create_agent function with empty tools list."""
        mock_yaml_load.return_value = mock_prompts
        mock_llm_instance = MagicMock()
        mock_get_llm.return_value = mock_llm_instance
        mock_agent_instance = MagicMock()
        mock_react_agent.return_value = mock_agent_instance

        session_id = "test-session"
        trace_id = "test-trace"
        empty_tools = []

        result = create_agent(session_id, trace_id, tools=empty_tools)

        mock_react_agent.assert_called_once_with(
            tools=empty_tools,
            llm=mock_llm_instance,
            system_prompt=mock_prompts["system_prompt"],
        )
        mock_agent_instance.update_prompts.assert_called_once_with(
            {
                "react_header": mock_prompts["header_prompt"],
            }
        )
        assert result == mock_agent_instance


class TestRunAgent:
    """Test cases for the run_agent function."""

    @pytest.fixture
    def agent(self):
        """Create a real ReActAgent for testing."""
        return create_agent(session_id="test-session", trace_id="test-trace")

    @pytest.fixture
    def inputs(self):
        return {"message": "Hello. How are you?"}

    @pytest.mark.asyncio
    async def test_run_agent_with_simple_input(self, agent, inputs):
        """Test run_agent function with simple string input."""
        results = []

        async for result in run_agent(agent, inputs, "trace-1", "session-1"):
            if isinstance(result, AgentStream):
                results.append(result.delta)
                break

        assert len(results) == 1
        assert results[0] == "Thought"

    @pytest.mark.asyncio
    async def test_run_agent_with_tags(self, agent, inputs):
        """Test run_agent function with complex input dictionary and tags."""
        results = []

        async for result in run_agent(
            agent, inputs, "trace-2", "session-2", tags=["tag1", "tag2"]
        ):
            if isinstance(result, AgentStream):
                results.append(result.delta)
                break

        assert len(results) == 1
        assert results[0] == "Thought"

    @pytest.mark.asyncio
    async def test_run_agent_with_empty_input(self, agent):
        """Test run_agent function with empty input."""
        empty_inputs = {}
        results = []

        async for result in run_agent(agent, empty_inputs, "trace-3", "session-3"):
            results.append(result)

        assert results is not None
