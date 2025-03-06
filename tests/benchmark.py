import os
import re
import sys
import uuid

import pytest
from langchain_core.messages import AIMessage

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath("unicef_geospatial"))

from agent.agent import create_agent, invoke_agent
from langfuse import Langfuse
from logging_config import get_logger
from utils.handlers import format_messages
from utils.initialize import initialize_earth_engine
from utils.types import Message

from tests.questions import hard_questions, medium_questions, simple_questions

logger = get_logger(__name__)
langfuse = Langfuse(
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    host=os.environ["LANGFUSE_HOST"],
)
# same run of tests share the session
session_id = str(uuid.uuid4())

initialize_earth_engine("ee_auth.json")


all_questions = {}
for question, answer in simple_questions.items():
    all_questions[question] = {"answer": answer, "category": "simple"}
for question, answer in medium_questions.items():
    all_questions[question] = {"answer": answer, "category": "medium"}
for question, answer in hard_questions.items():
    all_questions[question] = {"answer": answer, "category": "hard"}


def check_answer(question: str, answer: str) -> bool:
    """Check if the answer is correct."""
    expected_value = all_questions[question]["answer"]

    if expected_value in answer:
        return True

    numbers = re.findall(r"\d+(?:,\d+)*(?:\.\d+)?", answer)

    if not numbers:
        return False

    for number_str in numbers:
        try:
            clean_number = number_str.replace(",", "")
            value = float(clean_number)
            expected_float = float(expected_value)
            tolerance = expected_float * 0.01  # 1% tolerance

            if abs(expected_float - value) <= tolerance:
                return True
        except (ValueError, TypeError):
            continue

    return False


@pytest.mark.parametrize("question", list(all_questions.keys()))
@pytest.mark.asyncio
async def test_agent_question(question):
    """Test agent with a specific question."""
    trace_id = str(uuid.uuid4())
    message = Message(role="user", content=question, trace_id=trace_id)
    formatted_message = format_messages([message])

    category = all_questions[question]["category"]
    expected_answer = all_questions[question]["answer"]

    agent = create_agent(session_id=session_id, temperature=0.0, trace_id=trace_id)

    logger.info(
        f"Running agent with {category} question: {question}, session_id: {session_id}"
    )

    response = invoke_agent(
        agent,
        formatted_message,
        tags=["test", category],
        langfuse_observation_id=trace_id,
    )

    logger.info(f"Waiting for trace: {trace_id}")

    assert response is not None, f"No response found for question: {question}"

    for message in response["messages"][::-1]:
        if isinstance(message, AIMessage) and message.content:
            answer_content = message.content
            break

    is_correct = check_answer(question, answer_content)

    langfuse.score(
        trace_id=trace_id,
        name="answer_correctness",
        value="correct" if is_correct else "incorrect",
        comment=f"Expected: {expected_answer}, Got: {answer_content}",
    )

    assert is_correct, (
        f"Answer doesn't match expected value for question: {question}.\n"
        f"Expected: {expected_answer}\nGot: {answer_content}"
    )
