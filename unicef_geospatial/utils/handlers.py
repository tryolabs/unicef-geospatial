import ast
import json
import os
import shutil
from typing import AsyncGenerator

from llama_index.core.agent.workflow import AgentOutput, AgentStream, ToolCallResult
from llama_index.core.workflow import StopEvent
from logging_config import get_logger
from utils.constants import MAP_FILENAME
from utils.initialize import get_tools
from utils.types import Message, ReturnChunk

logger = get_logger(__name__)


def format_messages(chat_messages: list[Message]) -> dict[str, list[dict]]:
    """Format chat messages into the expected format for the agent.

    Args:
        chat_messages: List of Message objects containing role, content and trace_id

    Returns:
        Dictionary with 'messages' key containing list of formatted message dictionaries
    """
    messages = []
    for message in chat_messages:
        messages.append(
            {
                "role": message.role,
                "content": message.content,
                "trace_id": message.trace_id,
            }
        )

    return {"messages": messages}


async def handle_response(
    messages, trace_id, session_id, temp_dir: str = "", tags: list[str] = []
) -> AsyncGenerator[str, None]:
    """Handle the response by creating a temp directory, running respond, and cleaning up.

    Args:
        messages: List of messages to process
        trace_id: Unique identifier for tracing the request
        session_id: Unique identifier for the session
        temp_dir: Directory path for temporary files
        tags: List of tags for the request

    Yields:
        JSON serialized chunks of the response

    Cleans up the temporary directory after completion, even if an error occurs.
    """
    # Create the temp directory
    logger.info(f"Creating temp directory: {temp_dir}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        async for chunk in respond(messages, trace_id, session_id, temp_dir, tags):
            yield chunk
    finally:
        # Clean up the temp directory after the streaming is complete
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Removed temp directory: {temp_dir}")
        except OSError as e:
            logger.warning(
                f"Could not remove temp directory: {temp_dir} because of {e}"
            )


async def respond(
    messages, trace_id, session_id, temp_dir: str = "", tags: list[str] = []
):
    """Process messages and generate a response using the agent.

    Args:
        messages: List of messages to process
        trace_id: Unique identifier for tracing the request
        session_id: Unique identifier for the session
        temp_dir: Directory path for temporary files
        tags: List of tags for the request

    Yields:
        JSON serialized chunks of the response, including tool calls, agent streams,
        and the final answer
    """
    from agent.agent import create_agent, run_agent

    thinking_trace_id = f"th_{trace_id}"
    response_trace_id = f"r_{trace_id}"
    temperature = float(os.getenv("TEMPERATURE", 0.0))

    # Create agent with tools
    agent = create_agent(
        session_id=session_id,
        trace_id=thinking_trace_id,
        temperature=temperature,
        tools=get_tools(temp_dir),
    )

    is_final_answer = False
    is_thought_chunk = True
    async for chunk in run_agent(
        agent,
        messages,
        session_id=session_id,
        trace_id=thinking_trace_id,
        tags=tags,
    ):
        match chunk:
            case ToolCallResult():
                return_chunk = _process_tool_call_chunk(
                    chunk, thinking_trace_id, temp_dir
                )

            case AgentStream():
                if chunk.delta.startswith("Action"):
                    is_thought_chunk = False
                elif chunk.delta.startswith("Thought"):
                    is_thought_chunk = True

                # Skip non-thought chunks
                if not is_thought_chunk:
                    continue

                return_chunk = _process_agent_stream_chunk(chunk, thinking_trace_id)

            case StopEvent():
                # Signal that the thought is complete and the next chunk will be the response
                is_final_answer = True
                return_chunk = _process_stop_event(thinking_trace_id)

            case _ if is_final_answer:
                return_chunk = _process_final_answer(chunk, response_trace_id)

            case _:
                continue

        yield json.dumps(return_chunk.model_dump())
        yield "\n"

    # Signal that the response is complete
    return_chunk = ReturnChunk(trace_id=response_trace_id, is_finished=True)
    yield json.dumps(return_chunk.model_dump())
    yield "\n"


def _process_tool_call_chunk(
    chunk: ToolCallResult, thinking_trace_id: str, temp_dir: str
) -> ReturnChunk:
    """Process a tool call chunk and return the appropriate ReturnChunk.

    Args:
        chunk: ToolCallResult object containing tool name and output
        thinking_trace_id: Trace ID for the thinking phase
        temp_dir: Directory path for temporary files

    Returns:
        ReturnChunk object with tool call details and any HTML content

    Raises:
        Exception if there is an error processing the tool call
    """
    try:
        is_html = False
        html_content = ""
        content = ast.literal_eval(chunk.tool_output.content)

        input_arguments = content.get("input_arguments", {})
        tool_name = chunk.tool_name
        logger.info(f"Handling tool call: {tool_name}")

        if tool_name == "build_map":
            is_html = True
            with open(os.path.join(temp_dir, MAP_FILENAME), "r") as f:
                html_content = f.read()

        tool_call_message = f"Calling {tool_name}"
        if input_arguments:
            tool_call_message += " with arguments:\n" + "".join(
                [f"   {key}: {value}\n" for key, value in input_arguments.items()]
            )

        return ReturnChunk(
            tool_call=tool_call_message,
            trace_id=thinking_trace_id,
            is_html=is_html,
            html_content=html_content,
            thinking_chunk=True,
        )
    except Exception as e:
        logger.error(f"Error handling tool call: {e}")
        logger.error(f"Tool call: {chunk}")
        raise


def _process_agent_stream_chunk(
    chunk: AgentStream, thinking_trace_id: str
) -> ReturnChunk:
    """Process an agent stream chunk and return the appropriate ReturnChunk.

    Args:
        chunk: AgentStream object containing the delta response
        thinking_trace_id: Trace ID for the thinking phase

    Returns:
        ReturnChunk object with the processed response, adding a newline
        if the response ends with a closing brace
    """
    response = str(chunk.delta)

    # Send the actual response chunk
    return_chunk = ReturnChunk(response=response, trace_id=thinking_trace_id)

    if response.endswith("}"):
        # Insert a line break after action input
        return_chunk = ReturnChunk(
            response=f"{response}\n",
            trace_id=thinking_trace_id,
        )

    return return_chunk


def _process_stop_event(thinking_trace_id: str) -> ReturnChunk:
    """Process a stop event and return the appropriate ReturnChunk.

    Args:
        thinking_trace_id: Trace ID for the thinking phase

    Returns:
        ReturnChunk object indicating the thinking phase is finished
    """
    return ReturnChunk(trace_id=thinking_trace_id, is_finished=True)


def _process_final_answer(chunk, response_trace_id: str) -> ReturnChunk:
    """Process the final answer chunk and return the appropriate ReturnChunk.

    Args:
        chunk: Expected to be an AgentOutput object containing the final response
        response_trace_id: Trace ID for the response phase

    Returns:
        ReturnChunk object containing the final response content

    Logs an error if the chunk is not of type AgentOutput
    """
    if not isinstance(chunk, AgentOutput):
        logger.error(f"Unexpected chunk type: {type(chunk)}")
    return ReturnChunk(response=chunk.response.content, trace_id=response_trace_id)
