import os
from typing import Iterator

import litellm
from langchain.chat_models.base import BaseChatModel
from langchain.tools import BaseTool
from langchain_community.chat_models import ChatLiteLLM
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
    temperature: float = 0.0,
    tools: list[BaseTool] = get_tools(),
    system_prompt: str = system_prompt,
) -> CompiledGraph:
    """Create a LangGraph ReAct agent with the given LLM, tools and system prompt.

    Args:
        session_id: The session ID to use for the agent
        trace_id: The trace ID for tracking in Langfuse
        temperature: The temperature to use for the agent
        tools: List of tools available to the agent
        system_prompt: System prompt to provide context to the agent

    Returns:
        A compiled LangGraph agent ready to be invoked
    """
    return create_react_agent(
        tools=tools,
        model=get_llm(temperature, session_id, trace_id),
        state_modifier=system_prompt,
    )


@observe
def run_agent(
    agent: CompiledGraph,
    inputs: dict,
    tags: list[str] = [],
) -> Iterator[tuple[dict, str]]:
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


@observe
def invoke_agent(agent: CompiledGraph, inputs: dict, tags: list[str] = []) -> dict:
    """Invoke a LangGraph agent and return its response.

    Args:
        agent: The compiled LangGraph agent to invoke
        inputs: Dictionary of inputs to provide to the agent
        tags: List of tags to associate with the Langfuse trace

    Returns:
        The agent's complete response
    """
    langfuse_context.update_current_trace(tags=tags)
    return agent.invoke(inputs)
