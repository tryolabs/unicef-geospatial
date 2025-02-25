import json

from langchain_core.messages import AIMessage
from utils.types import Message


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


def extract_chain_of_thought(response: dict, input_length: int) -> list[str]:
    """Extract and format the chain of thought reasoning from agent messages.

    Args:
        response: Dictionary containing agent response messages
        input_length: Number of input messages to skip before extracting chain of thought

    Returns:
        List of strings containing the agent's reasoning steps and function calls
    """
    chain_of_thought = []
    for msg in response["messages"][input_length:-1]:
        if not isinstance(msg, AIMessage):
            continue

        # Add thought content
        if msg.content:
            chain_of_thought.append(msg.content)

        # Add function call information
        if "tool_calls" in msg.additional_kwargs:
            for tool_call in msg.additional_kwargs["tool_calls"]:
                function_args = json.loads(tool_call["function"]["arguments"])
                args_str = "\n".join(f"  {k}: {v}" for k, v in function_args.items())
                chain_of_thought.append(
                    f"Calling function {tool_call['function']['name']} with arguments:\n{args_str}"
                )

    return chain_of_thought


def process_html_content(response: dict) -> tuple[bool, str]:
    """Process HTML content from the agent response if present.

    Args:
        response: Dictionary containing agent response messages

    Returns:
        Tuple containing:
            - Boolean indicating if HTML content was found
            - String containing the HTML content if found, empty string otherwise
    """
    if len(response["messages"]) <= 1:
        return False, ""

    try:
        response_data = json.loads(response["messages"][-2].content)
        if path_to_map := response_data.get("path_to_map"):
            with open(path_to_map, "r") as f:
                return True, f.read()
    except json.JSONDecodeError:
        pass

    return False, ""
