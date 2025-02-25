import os

import uvicorn
from agent.agent import create_agent, run_agent
from fastapi.responses import HTMLResponse
from state import AppState
from utils.handlers import (
    extract_chain_of_thought,
    format_messages,
    process_html_content,
)
from utils.output import format_dict
from utils.types import Chat

app_state = AppState()
app = app_state.app


@app.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    app_state.logger.info("Serving index.html")
    return HTMLResponse(status_code=200)


@app.post("/ask")
def ask(chat: Chat) -> dict:
    app_state.logger.info(
        "Processing question: %s with session ID: %s",
        chat.chat_messages[-1].content,
        chat.session_id,
    )
    messages = format_messages(chat.chat_messages)
    app_state.logger.info("Running agent with inputs %s", format_dict(messages))

    # Create agent with session ID
    agent = create_agent(
        session_id=chat.session_id,
        temperature=app_state.params["llm"]["temperature"],
    )
    response, trace_id = run_agent(agent, messages)
    app_state.logger.info("Agent response: %s", format_dict(response))

    # Process response
    chain_of_thought = extract_chain_of_thought(response, len(messages["messages"]))
    is_html, html_content = process_html_content(response)

    return {
        "response": response["messages"][-1].content,
        "is_html": is_html,
        "html_content": html_content,
        "chain_of_thought": chain_of_thought,
        "trace_id": trace_id,
    }


if __name__ == "__main__":
    host = os.getenv("BACKEND_HOST")
    port = int(os.getenv("BACKEND_PORT"))
    app_state.logger.info("Starting server on http://%s:%s", host, port)
    uvicorn.run(app, host=host, port=port)
