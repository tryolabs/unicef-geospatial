import os
from typing import AsyncGenerator

import litellm
from langchain.chat_models.base import BaseChatModel
from langchain.tools import BaseTool
from langchain_community.chat_models import ChatLiteLLM
from langchain_core.messages import AIMessageChunk
from langfuse.decorators import langfuse_context, observe
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent
from utils.initialize import get_tools
from utils.prompts import system_prompt

litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]


def get_llm(temperature: float, session_id: str, trace_id: str) -> BaseChatModel:
    """Get the LLM model.

    Args:
        temperature: The temperature to use for the model
        session_id: The session ID to associate with this model
        trace_id: The trace ID for tracking in Langfuse

    Returns:
        A configured ChatLiteLLM instance
    """
    return ChatLiteLLM(
        model=os.getenv("MODEL_NAME", "gpt-4o-mini"),
        temperature=temperature,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model_kwargs={
            "metadata": {
                "session_id": session_id,
                "project_id": os.getenv("LANGFUSE_PROJECT_ID"),
                "trace_id": trace_id,
            }
        },
    )


def create_agent(
    session_id: str,
    trace_id: str,
    temp_dir: str = "",
    temperature: float = 0.0,
    tools: list[BaseTool] | None = None,
    system_prompt: str = system_prompt,
) -> CompiledGraph:
    """Create a LangGraph ReAct agent with the given LLM, tools and system prompt.

    Args:
        session_id: The session ID to use for the agent
        trace_id: The trace ID for tracking in Langfuse
        temperature: The temperature to use for the agent
        temp_dir: str ="" to temporary directory for storing files
        tools: List of tools available to the agent
        system_prompt: System prompt to provide context to the agent

    Returns:
        A compiled LangGraph agent ready to be invoked
    """
    if tools is None:
        tools = get_tools(temp_dir)

    return create_react_agent(
        tools=tools,
        model=get_llm(temperature, session_id, trace_id),
        state_modifier=system_prompt,
    )


@observe
async def run_agent(
    agent: CompiledGraph,
    inputs: dict,
    tags: list[str] = [],
) -> AsyncGenerator[tuple[dict, str], None]:
    """Run a LangGraph agent with the given inputs and stream the results.

    Args:
        agent: The compiled LangGraph agent to run
        inputs: Dictionary of inputs to provide to the agent
        tags: List of tags to associate with the Langfuse trace

    Yields:
        Chunks of the agent's response stream
    """
    langfuse_context.update_current_trace(tags=tags)
    for chunk in agent.stream(inputs, stream_mode="messages"):
        yield chunk


async def extract_response_from_chain_of_thought(
    messages: dict, full_response: str, session_id: str, trace_id: str
) -> AsyncGenerator[AIMessageChunk, None]:
    llm = get_llm(0.0, session_id, trace_id)
    prompt = """You are a helpful assistant.
    You are given the response from an agent in several steps of the thinking process and
    a conversation history.
    Your job is to generate a final response to the conversation history based on the
    response from the agent. It must be concise and answer the question.
    You can only use the information provided in the response from the agent.
    Do not add any information that is not provided in the response from the agent.
    Here is the conversation history:
    {conversation_history}
    Here is the response from the agent:
    {response}
    """
    prompt = prompt.format(conversation_history=messages, response=full_response)
    for chunk in llm.stream(prompt):
        yield chunk
