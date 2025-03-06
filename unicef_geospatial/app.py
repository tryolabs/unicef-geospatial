import uuid

from agent.agent import create_agent
from fastapi.responses import HTMLResponse, StreamingResponse
from state import AppState
from utils.handlers import format_messages, respond
from utils.output import format_dict
from utils.types import Chat

app_state = AppState()
app = app_state.app


@app.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    return HTMLResponse(status_code=200)


@app.post("/ask")
async def ask(chat: Chat) -> StreamingResponse:
    trace_id = str(uuid.uuid4())

    app_state.logger.info(
        "Processing question: %s with session ID: %s and trace ID: %s",
        chat.chat_messages[-1].content,
        chat.session_id,
        trace_id,
    )
    messages = format_messages(chat.chat_messages)
    app_state.logger.info("Running agent with inputs %s", format_dict(messages))

    # Create agent with session ID
    agent = create_agent(
        session_id=chat.session_id,
        trace_id=trace_id,
        temperature=app_state.params["llm"]["temperature"],
    )
    return StreamingResponse(
        respond(agent, messages, trace_id), media_type="text/event-stream"
    )
