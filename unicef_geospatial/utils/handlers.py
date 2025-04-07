import json
import os
import shutil
from typing import AsyncGenerator

from agent.agent import create_agent, extract_response_from_chain_of_thought, run_agent
from langchain_core.messages import AIMessageChunk, ToolMessage
from logging_config import get_logger
from utils.constants import MAP_FILENAME
from utils.types import Message, ReturnChunk

logger = get_logger(__name__)


def format_messages(chat_messages: list[Message]) -> dict[str, list[dict]]:
    """Format chat messages into the expected format for the agent.

    Args:
        chat_messages: List of alternating user and assistant messages from chat history
        question: The latest user question to append

    Returns:
        List of message dictionaries with role and content fields, formatted for the agent
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

    messages = {"messages": messages}

    return messages


async def respond(
    messages, trace_id, session_id, temp_dir: str = "", tags: list[str] = []
) -> AsyncGenerator[str, None]:
    # Create the temp directory
    logger.info(f"Creating temp directory: {temp_dir}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        thinking_trace_id = f"th_{trace_id}"
        temperature = float(os.getenv("TEMPERATURE", 0.0))
        agent = create_agent(
            session_id=session_id,
            trace_id=thinking_trace_id,
            temperature=temperature,
            temp_dir=temp_dir,
        )
        full_response = ""
        async for chunk in run_agent(
            agent, messages, langfuse_observation_id=thinking_trace_id, tags=tags
        ):
            if isinstance(chunk[0], ToolMessage):
                try:
                    return_chunk = handle_tool_call(
                        chunk[0], thinking_trace_id, temp_dir
                    )
                except Exception as e:
                    logger.error(f"Error handling tool call: {e}")
                    logger.error(f"Tool call: {chunk[0]}")
                    pass

            elif isinstance(chunk[0], AIMessageChunk):
                response = str(chunk[0].content)
                full_response += response
                return_chunk = ReturnChunk(
                    response=response,
                    trace_id=thinking_trace_id,
                    tool_call="",
                    is_html=False,
                    html_content="",
                    is_finished=False,
                )

            yield json.dumps(return_chunk.model_dump())
            yield "\n"

        # Signal that the response is complete
        return_chunk = ReturnChunk(
            response="",
            trace_id=thinking_trace_id,
            tool_call="",
            is_html=False,
            html_content="",
            is_finished=True,
        )
        yield json.dumps(return_chunk.model_dump())
        yield "\n"

        response_trace_id = f"r_{trace_id}"

        async for chunk in extract_response_from_chain_of_thought(
            messages, full_response, session_id, response_trace_id
        ):
            yield json.dumps(
                ReturnChunk(
                    response=chunk.content,
                    trace_id=response_trace_id,
                    tool_call="",
                    is_html=False,
                    html_content="",
                    is_finished=False,
                ).model_dump()
            )
            yield "\n"

        return_chunk = ReturnChunk(
            response="",
            trace_id=response_trace_id,
            tool_call="",
            is_html=False,
            html_content="",
            is_finished=True,
        )
        yield json.dumps(return_chunk.model_dump())
        yield "\n"
    finally:
        # Clean up the temp directory after the streaming is complete
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Removed temp directory: {temp_dir}")
        except OSError as e:
            logger.warning(
                f"Could not remove temp directory: {temp_dir} because of {e}"
            )


def handle_tool_call(
    tool_message: ToolMessage, trace_id: str, temp_dir: str = ""
) -> ReturnChunk:
    is_html = False
    html_content = ""
    content = json.loads(tool_message.content)

    input_arguments = content.get("input_arguments", {})
    tool_name = tool_message.name
    if tool_name == "build_map":
        is_html = True
        with open(os.path.join(temp_dir, MAP_FILENAME), "r") as f:
            html_content = f.read()

    tool_call_message = f"Calling {tool_name}"
    if input_arguments != {}:
        tool_call_message += " with arguments:\n" + "".join(
            [f"   {key}: {value}\n" for key, value in input_arguments.items()]
        )

    return ReturnChunk(
        response="",
        tool_call=tool_call_message,
        trace_id=trace_id,
        is_html=is_html,
        html_content=html_content,
        is_finished=False,
        thinking_chunk=True,
    )
