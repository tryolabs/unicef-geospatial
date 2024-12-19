from pathlib import Path

import yaml
from agent.agent import create_agent, run_agent
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from logging_config import get_logger
from pydantic import BaseModel
from utils.initialize import get_llm, get_tools, initialize_earth_engine
from utils.prompts import system_prompt

app = FastAPI()

# Mount static files
app.mount(
    "/static", StaticFiles(directory="unicef_geospatial/frontend/static"), name="static"
)

params_path = Path("unicef_geospatial/params.yaml")
with params_path.open("r") as f:
    params = yaml.safe_load(f)

logger = get_logger(__name__)
logger.info("Loading application with project %s", params["ee"]["project"])

initialize_earth_engine(params["ee"]["project"])

tools = get_tools()
llm = get_llm(params["llm"]["temperature"])
agent = create_agent(llm, tools, system_prompt)

# Mount templates directory
templates = Jinja2Templates(directory="unicef_geospatial/frontend/templates")


class Question(BaseModel):
    question: str


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/ask")
def ask(question: Question) -> dict:
    logger.info("Processing question: %s", question.question)
    inputs = {
        "messages": [
            {
                "role": "user",
                "content": question.question,
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
