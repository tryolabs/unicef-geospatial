import os
import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from state import AppState
from utils.constants import BASE_PATH
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
    session_id = chat.session_id
    temp_dir = os.path.join(BASE_PATH, f"{session_id}")

    app_state.logger.info(
        "Processing question: %s with session ID: %s and trace ID: %s",
        chat.chat_messages[-1].content,
        session_id,
        trace_id,
    )
    messages = format_messages(chat.chat_messages)
    app_state.logger.info("Running agent with inputs %s", format_dict(messages))

    return StreamingResponse(
        respond(
            messages,
            trace_id,
            session_id,
            temp_dir,
        ),
        media_type="text/event-stream",
    )
