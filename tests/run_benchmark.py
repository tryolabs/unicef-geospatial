import json
import os
import sys
import uuid

import pytest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath("unicef_geospatial"))

from datetime import datetime

from langfuse import Langfuse
from logging_config import get_logger
from utils.constants import BASE_PATH
from utils.handlers import format_messages, respond
from utils.initialize import initialize_earth_engine
from utils.types import Message

from tests.test_data import benchmark_list, extract_number_from_response

logger = get_logger(__name__)
langfuse = Langfuse(
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    host=os.environ["LANGFUSE_HOST"],
)

# Define path for test results and session ID file
RESULTS_PATH = "tests/results"

if not os.path.exists(RESULTS_PATH):
    os.makedirs(RESULTS_PATH)

# Use a file to share session ID across processes
SESSION_FILE = os.path.join(RESULTS_PATH, ".session_id")

# Read existing session ID or create a new one
try:
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            session_id = f.read().strip()
            logger.info(f"Using existing session ID: {session_id}")
    else:
        session_id = str(uuid.uuid4())
        with open(SESSION_FILE, "w") as f:
            f.write(session_id)
            logger.info(f"Created new session ID: {session_id}")
except Exception as e:
    logger.error(f"Error handling session ID file: {e}")
    session_id = str(uuid.uuid4())
    logger.info(f"Using fallback session ID: {session_id}")

initialize_earth_engine("ee_auth.json")

# Create results file
RESULTS_FILE = f"{RESULTS_PATH}/results_{datetime.now().strftime('%Y%m%d_%H:%M')}.tsv"
if os.path.exists(RESULTS_FILE):
    os.remove(RESULTS_FILE)

with open(RESULTS_FILE, "w") as fh:
    logger.info(f"Writing results to {RESULTS_FILE}")
    fh.write("correct\tquestion\tvariation\texpected\tvalue\tanswer\n")


# all_questions = {}
# for question, answer in simple_questions.items():
#     all_questions[question] = {"answer": answer, "category": "simple"}
# for question, answer in medium_questions.items():
#     all_questions[question] = {"answer": answer, "category": "medium"}
# for question, answer in hard_questions.items():
#     all_questions[question] = {"answer": answer, "category": "hard"}


@pytest.mark.parametrize("question,expected,variation", benchmark_list)
@pytest.mark.asyncio
async def test_agent_question(question, expected, variation):
    """Test agent with a specific question."""
    trace_id = str(uuid.uuid4())
    message = Message(role="user", content=question, trace_id=trace_id)
    formatted_message = format_messages([message])
    temp_dir = os.path.join(BASE_PATH, f"{trace_id}")

    final_answer = ""
    async for chunk in respond(
        formatted_message, trace_id, session_id, temp_dir, tags=["benchmark"]
    ):
        try:
            chunk = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if chunk.get("trace_id", "").startswith("r_"):
            final_answer += chunk.get("response", "")

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
