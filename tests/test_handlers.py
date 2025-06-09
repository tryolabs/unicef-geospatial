"""
Unit tests for the handlers module.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from utils.schemas import Message, ReturnChunk

from unicef_geospatial.utils.handlers import (
    _format_messages,
    _process_agent_stream_chunk,
    _process_final_answer,
    _process_stop_event,
    _process_tool_call_chunk,
    handle_response,
    respond,
)


class TestFormatMessages:
    """Test cases for the format_messages function."""

    def test_format_messages_single_message(self):
        """Test formatting a single message."""
        messages = [
            Message(
                content="Hello, how can I help?", role="assistant", trace_id="trace-123"
            )
        ]

        result = _format_messages(messages)

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0]["content"] == "Hello, how can I help?"
        assert result["messages"][0]["role"] == "assistant"
        assert result["messages"][0]["trace_id"] == "trace-123"

    def test_format_messages_multiple_messages(self):
        """Test formatting multiple messages."""
        messages = [
            Message(content="Hi", role="user", trace_id="trace-1"),
            Message(content="Hello!", role="assistant", trace_id="trace-2"),
            Message(content="How are you?", role="user", trace_id="trace-3"),
        ]

        result = _format_messages(messages)

        assert len(result["messages"]) == 3
        assert result["messages"][0]["content"] == "Hi"
        assert result["messages"][1]["content"] == "Hello!"
        assert result["messages"][2]["content"] == "How are you?"

    def test_format_messages_empty_list(self):
        """Test formatting an empty message list."""
        messages = []

        result = _format_messages(messages)

        assert "messages" in result
        assert len(result["messages"]) == 0

    def test_format_messages_preserves_all_fields(self):
        """Test that all message fields are preserved in formatting."""
        messages = [
            Message(
                content="Test message with special chars @#$%",
                role="user",
                trace_id="special-trace-456",
            )
        ]

        result = _format_messages(messages)

        formatted_message = result["messages"][0]
        assert formatted_message["content"] == "Test message with special chars @#$%"
        assert formatted_message["role"] == "user"
        assert formatted_message["trace_id"] == "special-trace-456"


class TestChunkProcessing:
    """Test cases for chunk processing functions."""

    def test_process_tool_call_chunk_basic(self):
        """Test processing a basic tool call chunk."""
        mock_chunk = MagicMock()
        mock_chunk.tool_name = "test_tool"
        mock_chunk.tool_output.content = "{'input_arguments': {'param': 'value'}}"
        mock_chunk.response.content

        result = _process_tool_call_chunk(mock_chunk, "trace-123", "/tmp/test")

        assert isinstance(result, ReturnChunk)
        assert result.trace_id == "trace-123"
        assert "Calling test_tool" in result.tool_call
        assert "param: value" in result.tool_call

    def test_process_tool_call_chunk_no_arguments(self):
        """Test processing a tool call chunk with no input arguments."""
        mock_chunk = MagicMock()
        mock_chunk.tool_name = "simple_tool"
        mock_chunk.tool_output.content = "{}"

        result = _process_tool_call_chunk(mock_chunk, "trace-789", "/tmp/test")

        assert result.tool_call == "Calling simple_tool"

    def test_process_agent_stream_chunk(self):
        """Test processing an agent stream chunk."""
        mock_chunk = MagicMock()
        mock_chunk.delta = "This is a test response"

        result = _process_agent_stream_chunk(mock_chunk, "trace-stream")

        assert isinstance(result, ReturnChunk)
        assert result.trace_id == "trace-stream"
        assert result.response == "This is a test response"

    def test_process_stop_event(self):
        """Test processing a stop event."""
        result = _process_stop_event("trace-stop")

        assert isinstance(result, ReturnChunk)
        assert result.trace_id == "trace-stop"

    def test_process_final_answer(self):
        """Test processing a final answer."""
        mock_chunk = MagicMock()
        mock_chunk.response.content = "This is the final answer"

        result = _process_final_answer(mock_chunk, "trace-final")

        assert isinstance(result, ReturnChunk)
        assert result.trace_id == "trace-final"
        assert result.response == "This is the final answer"


class TestIntegrationAndErrors:
    """Test cases for integration and error handling."""

    @pytest.mark.asyncio
    async def test_respond_integration(self):
        """Test the respond function integration."""
        messages = {"messages": [{"content": "test", "role": "user"}]}
        trace_id = "test-respond"
        session_id = "test-session"
        temp_dir = "tests/data/test_temp"

        responses = []
        async for response in respond(messages, trace_id, session_id, temp_dir):
            responses.append(response)

        assert len(responses) > 0

    @pytest.mark.asyncio
    async def test_handle_response_logging_on_cleanup_error(self):
        """Test that cleanup errors are logged but don't raise."""
        messages = [Message(content="test", role="user", trace_id="test-trace")]
        trace_id = "test-trace"
        session_id = "test-session"
        temp_dir = "tests/data/test_temp"

        chunks = []
        async for chunk in handle_response(messages, trace_id, session_id, temp_dir):
            chunks.append(chunk)

        assert len(chunks) > 0
