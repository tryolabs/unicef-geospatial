from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from unicef_geospatial.agent.agent import create_agent, run_agent
from unicef_geospatial.heatwaves.tools import (
    get_heatwave_metric_for_admin_level_1,
    get_heatwave_metric_for_country,
)
from unicef_geospatial.utils.initialize import get_llm, initialize_earth_engine
from unicef_geospatial.utils.prompts import system_prompt

app = FastAPI()
params_path = Path("unicef_geospatial/params.yaml")
with params_path.open("r") as f:
    params = yaml.safe_load(f)

initialize_earth_engine(params["ee"]["project"])

tools = [get_heatwave_metric_for_country, get_heatwave_metric_for_admin_level_1]

llm = get_llm(params["llm"]["temperature"])
agent = create_agent(llm, tools, system_prompt)

# Mount templates directory
templates = Jinja2Templates(directory="unicef_geospatial/templates")


class Question(BaseModel):
    question: str


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/ask")
def ask(question: Question) -> dict:
    inputs = {
        "messages": [
            {
                "role": "user",
                "content": question.question,
            }
        ]
    }
    response = run_agent(agent, inputs)
    return {"response": response["messages"][-1].content}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
