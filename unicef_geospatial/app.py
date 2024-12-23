import logging
from pathlib import Path

import yaml
from agent.agent import create_agent, run_agent
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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

    # Load parameters
    params_path = Path("unicef_geospatial/params.yaml")
    with params_path.open("r") as f:
        params = yaml.safe_load(f)

    logger = get_logger(__name__)
    logger.info("Loading application with project %s", params["ee"]["project"])

    # Initialize components
    initialize_earth_engine(params["ee"]["project"])
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

    html_content = ""
    is_html = False
    if len(response["messages"]) > 1:
        html_content = response["messages"][-2].content
        is_html = html_content.startswith("<!DOCTYPE html>")

    return {"response": content, "is_html": is_html, "html_content": html_content}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
