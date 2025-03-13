import json
from typing import AsyncGenerator

from agent.agent import get_llm, run_agent
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


async def respond(agent, messages, trace_id, session_id) -> AsyncGenerator[str, None]:
    full_response = ""
    for chunk in run_agent(agent, messages, langfuse_observation_id=trace_id):
        if isinstance(chunk[0], ToolMessage):
            try:
                return_chunk = handle_tool_call(chunk[0], trace_id)
            except Exception as e:
                logger.error(f"Error handling tool call: {e}")
                logger.error(f"Tool call: {chunk[0]}")
                pass

        elif isinstance(chunk[0], AIMessageChunk):
            response = str(chunk[0].content)
            full_response += response
            return_chunk = ReturnChunk(
                response=response,
                trace_id=trace_id,
                tool_call="",
                is_html=False,
                html_content="",
                is_finished=False,
                thinking_chunk=True,
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
        thinking_chunk=True,
    )
    yield json.dumps(return_chunk.model_dump())

    llm = get_llm(0.0, session_id, trace_id)
    prompt = """You are a helpful assistant.
    You are given the response from an agent in several steps of the thinking process and
    a conversation history.
    Your job is to generate a final response to the conversation history based on the
    response from the agent. It must be concise and answer the question.
    Here is the conversation history:
    {conversation_history}
    Here is the response from the agent:
    {response}
    """
    prompt = prompt.format(conversation_history=messages, response=full_response)
    for chunk in llm.stream(prompt):
        yield json.dumps(
            ReturnChunk(
                response=chunk.content,
                trace_id=trace_id,
                tool_call="",
                is_html=False,
                html_content="",
                is_finished=False,
                thinking_chunk=False,
            ).model_dump()
        )
        yield "\n"

    return_chunk = ReturnChunk(
        response="",
        trace_id=trace_id,
        tool_call="",
        is_html=False,
        html_content="",
        is_finished=True,
        thinking_chunk=False,
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
