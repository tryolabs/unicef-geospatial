import json
from typing import AsyncGenerator

from agent.agent import run_agent
from langchain_core.messages import AIMessageChunk, ToolMessage
from logging_config import get_logger
from utils.constants import PATH_TO_MAP
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


async def respond(agent, messages) -> AsyncGenerator[str, None]:
    for chunk, trace_id in run_agent(agent, messages):
        if isinstance(chunk[0], ToolMessage):
            return_chunk = handle_tool_call(chunk[0], trace_id)

        elif isinstance(chunk[0], AIMessageChunk):
            response = str(chunk[0].content)
            return_chunk = ReturnChunk(
                response=response,
                trace_id=trace_id,
                tool_call="",
                is_html=False,
                html_content="",
            )

        yield json.dumps(return_chunk.model_dump())
        yield "\n"

    # Signal that the response is complete
    return_chunk = ReturnChunk(
        response="",
        trace_id=trace_id,
        tool_call="",
        is_html=False,
        html_content="",
        is_finished=True,
    )

    yield json.dumps(return_chunk.model_dump())


def handle_tool_call(tool_message: ToolMessage, trace_id: str) -> ReturnChunk:
    is_html = False
    html_content = ""
    content = json.loads(tool_message.content)

    input_arguments = content.get("input_arguments", {})
    tool_name = tool_message.name
    if tool_name == "build_map":
        is_html = True
        with open(PATH_TO_MAP, "r") as f:
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
    )
