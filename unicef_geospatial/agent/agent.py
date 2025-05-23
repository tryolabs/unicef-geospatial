import os
from typing import AsyncGenerator, Callable

import litellm
import yaml
from langfuse.llama_index import LlamaIndexInstrumentor
from llama_index.core.agent.workflow import ReActAgent
from llama_index.llms.litellm import LiteLLM

litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]

instrumentor = LlamaIndexInstrumentor()

with open("unicef_geospatial/utils/prompts.yaml", "r") as f:
    prompts = yaml.safe_load(f)

header_prompt = prompts["header_prompt"]
system_prompt = prompts["system_prompt"]


def get_llm(temperature: float, session_id: str, trace_id: str) -> LiteLLM:
    """Get the LLM model.

    Args:
        temperature: The temperature to use for the model
        session_id: The session ID to associate with this model
        trace_id: The trace ID for tracking in Langfuse

    Returns:
        A configured ChatLiteLLM instance
    """
    return LiteLLM(
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
    temperature: float = 0.0,
    tools: list[Callable] | None = None,
    system_prompt: str = system_prompt,
) -> ReActAgent:
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
    agent = ReActAgent(
        tools=tools,
        llm=get_llm(temperature, session_id, trace_id),
        system_prompt=system_prompt,
    )

    agent.update_prompts(
        {
            "react_header": header_prompt,
        }
    )

    return agent


async def run_agent(
    agent: ReActAgent,
    inputs: dict,
    trace_id: str,
    session_id: str,
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
    instrumentor.start()
    handler = agent.run(str(inputs))

    with instrumentor.observe(trace_id=trace_id, session_id=session_id, tags=tags):
        async for chunk in handler.stream_events():
            yield chunk

        response = await handler

    instrumentor.flush()

    yield response
