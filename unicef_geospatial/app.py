import os
import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from state import AppState
from utils.auth import (
    Token,
    User,
    authenticate_user,
    create_access_token,
    get_current_user,
)
from utils.constants import BASE_PATH
from utils.handlers import format_messages, handle_response
from utils.io import format_dict
from utils.types import Chat

app_state = AppState()
app = app_state.app


@app.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    return HTMLResponse(status_code=200)


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    )
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
    }


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@app.post("/ask")
async def ask(
    chat: Chat, current_user: Annotated[User, Depends(get_current_user)]
) -> StreamingResponse:

    if chat.chat_messages == [] or chat.chat_messages[-1].content == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Chat messages cannot be empty",
        )

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
        handle_response(
            messages,
            trace_id,
            session_id,
            temp_dir,
        ),
        media_type="text/event-stream",
    )
