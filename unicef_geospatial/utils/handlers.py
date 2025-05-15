import ast
import json
import os
import shutil
from typing import AsyncGenerator

from agent.agent import create_agent, run_agent
from llama_index.core.agent.workflow import AgentOutput, AgentStream, ToolCallResult
from llama_index.core.workflow import StopEvent
from logging_config import get_logger
from utils.constants import MAP_FILENAME
from utils.initialize import get_tools
from utils.types import Message, ReturnChunk

logger = get_logger(__name__)


def format_messages(chat_messages: list[Message]) -> dict[str, list[dict]]:
    """Format chat messages into the expected format for the agent."""
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
    """Handle the response by creating a temp directory, running respond, and cleaning up."""
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
    """Process messages and generate a response using the agent."""
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

    full_response = ""
    is_final_answer = False

    async for chunk in run_agent(
        agent,
        messages,
        session_id=session_id,
        langfuse_observation_id=thinking_trace_id,
        tags=tags,
    ):
        match chunk:
            case ToolCallResult():
                try:
                    return_chunk = handle_tool_call(chunk, thinking_trace_id, temp_dir)
                except Exception as e:
                    logger.error(f"Error handling tool call: {e}")
                    logger.error(f"Tool call: {chunk}")

            case AgentStream():
                response = str(chunk.delta)
                full_response += response

                # Send the actual response chunk
                return_chunk = ReturnChunk(
                    response=response, trace_id=thinking_trace_id
                )

                if response.endswith("}"):
                    # Insert a line break after action input
                    return_chunk = ReturnChunk(
                        response=f"{response}\n",
                        trace_id=thinking_trace_id,
                    )

            case StopEvent():
                # Signal that the thought is complete and the next chunk will be the response
                is_final_answer = True
                return_chunk = ReturnChunk(trace_id=thinking_trace_id, is_finished=True)

            case _ if is_final_answer:
                if not isinstance(chunk, AgentOutput):
                    logger.error(f"Unexpected chunk type: {type(chunk)}")
                return_chunk = ReturnChunk(
                    response=chunk.response.content, trace_id=response_trace_id
                )

            case _:
                continue

        yield json.dumps(return_chunk.model_dump())
        yield "\n"

    # Signal that the response is complete
    return_chunk = ReturnChunk(trace_id=response_trace_id, is_finished=True)
    yield json.dumps(return_chunk.model_dump())
    yield "\n"


def handle_tool_call(
    tool_message: ToolCallResult, trace_id: str, temp_dir: str = ""
) -> ReturnChunk:
    """Handle a tool call and return the appropriate ReturnChunk."""
    is_html = False
    html_content = ""
    content = ast.literal_eval(tool_message.tool_output.content)

    input_arguments = content.get("input_arguments", {})
    tool_name = tool_message.tool_name
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
        trace_id=trace_id,
        is_html=is_html,
        html_content=html_content,
        thinking_chunk=True,
    )
