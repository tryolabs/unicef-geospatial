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
    new_query: str
    previous_messages: list[str] | None = None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/ask")
def ask(chat: Chat) -> dict:
    logger.info("Processing question: %s", chat.new_query)
    previous_messages = []
    for i, message in enumerate(chat.previous_messages):
        role = "user" if i % 2 == 0 else "system"
        previous_messages.append({"role": role, "content": message})

    inputs = {
        "messages": previous_messages
        + [
            {
                "role": "user",
                "content": chat.new_query,
            }
        ]
    }
    logger.info("Running agent with inputs")
    response = run_agent(agent, inputs)

    content = response["messages"][-1].content

    # Check if the content is HTML (from map tool)
    html_content = response["messages"][-2].content
    is_html = html_content.startswith("<!DOCTYPE html>")

    logger.info("Agent response received")
    return {"response": content, "is_html": is_html, "html_content": html_content}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
