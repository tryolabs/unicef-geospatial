import os
import re
import sys
import uuid

import pytest
from langchain_core.messages import AIMessageChunk

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath("unicef_geospatial"))

from datetime import datetime

from agent.agent import create_agent, run_agent
from langfuse import Langfuse
from logging_config import get_logger
from utils.handlers import format_messages
from utils.initialize import initialize_earth_engine
from utils.types import Message

from tests.questions import hard_questions, medium_questions, simple_questions
from unicef_geospatial.agent.agent import extract_response_from_chain_of_thought

logger = get_logger(__name__)
langfuse = Langfuse(
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    host=os.environ["LANGFUSE_HOST"],
)
# same run of tests share the session
session_id = str(uuid.uuid4())

initialize_earth_engine("ee_auth.json")

RESULTS_PATH = "tests/results"

if not os.path.exists(RESULTS_PATH):
    os.makedirs(RESULTS_PATH)

RESULTS_FILE = f"{RESULTS_PATH}/results_{datetime.now().strftime('%Y%m%d_%H:%M')}.tsv"
if os.path.exists(RESULTS_FILE):
    os.remove(RESULTS_FILE)

with open(RESULTS_FILE, "w") as fh:
    logger.info(f"Writing results to {RESULTS_FILE}")
    fh.write("correct\tquestion\tvariation\texpected\tvalue\tanswer\n")

from tests.test_data import benchmark_list, extract_number_from_response

# all_questions = {}
# for question, answer in simple_questions.items():
#     all_questions[question] = {"answer": answer, "category": "simple"}
# for question, answer in medium_questions.items():
#     all_questions[question] = {"answer": answer, "category": "medium"}
# for question, answer in hard_questions.items():
#     all_questions[question] = {"answer": answer, "category": "hard"}


def check_answer(
    question: str, answer: str, expected_value: int
) -> tuple[bool, int | None]:
    """Check if the answer is correct."""
    # expected_value = all_questions[question]["answer"]

    if str(expected_value) in answer:
        return True, expected_value

    numbers = re.findall(r"\d+(?:,\d+)*(?:\.\d+)?", answer)

    if not numbers:
        return False, None

    for number_str in numbers:
        try:
            clean_number = number_str.replace(",", "")
            value = float(clean_number)
            expected_float = float(expected_value)
            tolerance = expected_float * 0.01  # 1% tolerance

            if abs(expected_float - value) <= tolerance:
                return True, value
        except (ValueError, TypeError):
            continue

    return False, None


@pytest.mark.parametrize("question,expected,variation", benchmark_list)
@pytest.mark.asyncio
async def test_agent_question(question, expected, variation):
    """Test agent with a specific question."""
    trace_id = str(uuid.uuid4())
    message = Message(role="user", content=question, trace_id=trace_id)
    formatted_message = format_messages([message])

    agent = create_agent(session_id=session_id, temperature=0.0, trace_id=trace_id)

    full_response = ""
    async for chunk in run_agent(
        agent,
        formatted_message,
        tags=["test"],
        langfuse_observation_id=trace_id,
    ):
        if isinstance(chunk[0], AIMessageChunk):
            full_response += chunk[0].content

    logger.info(f"Waiting for trace: {trace_id}")

    assert full_response is not None, f"No response found for question: {question}"

    response_trace_id = f"r_{trace_id}"

    final_answer = ""
    async for chunk in extract_response_from_chain_of_thought(
        formatted_message, full_response, session_id, response_trace_id
    ):
        final_answer += chunk.content

    numerical_value = extract_number_from_response(question, final_answer)
    if numerical_value is None:
        is_correct = False
    else:
        tolerance = expected * 0.01
        is_correct = abs(numerical_value - expected) <= tolerance

    with open(RESULTS_FILE, "a+") as fh:
        answer = final_answer.replace("\n", "||")
        fh.write(
            f"{is_correct}\t{question}\t{variation}\t{expected}\t{numerical_value}\t{answer}\n"
        )

    langfuse.score(
        trace_id=trace_id,
        name="answer_correctness",
        value="correct" if is_correct else "incorrect",
        comment=f"Expected: {expected}, Got: {final_answer}",
    )

    assert (
        is_correct
    ), f"Answer doesn't match expected value for question: {question}\n\
        Expected: {expected}\nGot: {numerical_value}\n\
        Full answer: {answer}"
