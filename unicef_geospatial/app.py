import json
import logging
from pathlib import Path

import yaml
from agent.agent import create_agent, run_agent
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langchain_core.messages import AIMessage
from langgraph.graph.graph import CompiledGraph
from logging_config import get_logger
from pydantic import BaseModel
from utils.initialize import get_llm, get_tools, initialize_earth_engine
from utils.output import format_dict
from utils.prompts import system_prompt

app = FastAPI()


def init_app() -> tuple[dict, logging.Logger, CompiledGraph, Jinja2Templates]:
    # Mount static files
    app.mount(
        "/static",
        StaticFiles(directory="unicef_geospatial/frontend/static"),
        name="static",
    )

    load_dotenv(override=True)

    # Load parameters
    params_path = Path("unicef_geospatial/params.yaml")
    with params_path.open("r") as f:
        params = yaml.safe_load(f)

    logger = get_logger(__name__)
    logger.info("Loading application with project")

    # Initialize components
    initialize_earth_engine()
    tools = get_tools()
    llm = get_llm(params["llm"]["temperature"])
    agent = create_agent(llm, tools, system_prompt)

    # Mount templates
    templates = Jinja2Templates(directory="unicef_geospatial/frontend/templates")

    return params, logger, agent, templates


params, logger, agent, templates = init_app()


class Chat(BaseModel):
    chat_messages: list[str]


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/ask")
def ask(chat: Chat) -> dict:
    question = chat.chat_messages.pop(-1)
    logger.info("Processing question: %s", question)
    previous_messages = []
    for i, message in enumerate(chat.chat_messages or []):
        role = "user" if i % 2 == 0 else "assistant"
        previous_messages.append({"role": role, "content": message})

    inputs = {
        "messages": previous_messages
        + [
            {
                "role": "user",
                "content": question,
            }
        ]
    }
    logger.info("Running agent with inputs %s", format_dict(inputs))
    response = run_agent(agent, inputs)

    logger.info("Agent response: %s", format_dict(response))

    content = response["messages"][-1].content

    # Extract chain of thought from intermediate messages
    chain_of_thought = []
    for msg in response["messages"][len(inputs["messages"]) : -1]:
        if isinstance(msg, AIMessage):
            try:
                thought = json.loads(msg.content)
                chain_of_thought.append(thought)
            except json.JSONDecodeError:
                chain_of_thought.append(msg.content)

            function_name = msg.additional_kwargs["tool_calls"][0]["function"]["name"]
            function_args = msg.additional_kwargs["tool_calls"][0]["function"][
                "arguments"
            ]
            function_args_str = "\n".join(
                f"  {k}: {v}" for k, v in json.loads(function_args).items()
            )
            chain_of_thought.append(
                f"Calling function {function_name} with arguments:\n{function_args_str}"
            )

    html_content = ""
    is_html = False
    if len(response["messages"]) > 1:
        response_data = response["messages"][-2].content
        try:
            response_data = json.loads(response_data)
            is_html = response_data.get("path_to_map") is not None
            if is_html:
                with open(response_data["path_to_map"], "r") as f:
                    html_content = f.read()

        except json.JSONDecodeError:
            pass

    return {
        "response": content,
        "is_html": is_html,
        "html_content": html_content,
        "chain_of_thought": chain_of_thought,
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
