from langchain.chat_models.base import BaseChatModel
from langchain.tools import BaseTool
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent

from unicef_geospatial.utils.output import print_stream


def create_agent(
    llm: BaseChatModel, tools: list[BaseTool], system_prompt: str
) -> CompiledGraph:
    """Create a LangGraph ReAct agent with the given LLM, tools and system prompt.

    Args:
        llm: The LLM to use for the agent
        tools: List of tools available to the agent
        system_prompt: System prompt to provide context to the agent

    Returns:
        A compiled LangGraph agent ready to be invoked
    """
    return create_react_agent(
        tools=tools,
        model=llm,
        state_modifier=system_prompt,
    )


def run_agent(agent: CompiledGraph, inputs: dict) -> dict:
    """Run a LangGraph agent with the given inputs.

    Args:
        agent: The compiled LangGraph agent to run
        inputs: Dictionary of inputs to provide to the agent

    Returns:
        Dictionary containing the agent's response
    """
    return agent.invoke(inputs)


def run_and_print_stream(agent: CompiledGraph, inputs: dict) -> None:
    """Run a LangGraph agent and print its response stream.

    Args:
        agent: The compiled LangGraph agent to run
        inputs: Dictionary of inputs to provide to the agent
    """
    print_stream(agent.stream(inputs, stream_mode="values"))
