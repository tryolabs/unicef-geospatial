import json
import os
import sys
import uuid

import pytest
import yaml
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath("unicef_geospatial"))

from datetime import datetime

from langfuse import Langfuse
from logging_config import get_logger
from utils.constants import BASE_PATH
from utils.handlers import format_messages, respond
from utils.initialize import initialize_earth_engine
from utils.types import Message

from tests.test_data import (
    benchmark_list,
    extract_number_from_response,
    score_textual_answer,
)

load_dotenv(override=True)

logger = get_logger(__name__)

with open(os.environ["PATH_TO_LANGFUSE_SECRET_KEY"], "r") as f:
    secret_key = f.read().strip()

langfuse = Langfuse(
    secret_key=secret_key,
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    host=os.environ["LANGFUSE_HOST"],
)


with open(os.environ["PATH_TO_LLM_API_KEY"], "r") as f:
    os.environ["OPENAI_API_KEY"] = f.read().strip()

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

initialize_earth_engine(os.environ["PATH_TO_EE_AUTH"])

# Create results file
NUMERICAL_RESULTS_FILE = (
    f"{RESULTS_PATH}/numerical/results_{datetime.now().strftime('%Y%m%d_%H:%M')}.tsv"
)
TEXTUAL_RESULTS_FILE = (
    f"{RESULTS_PATH}/textual/results_{datetime.now().strftime('%Y%m%d_%H:%M')}.tsv"
)
for file in [NUMERICAL_RESULTS_FILE, TEXTUAL_RESULTS_FILE]:
    if not os.path.exists(os.path.dirname(file)):
        os.makedirs(os.path.dirname(file))
    if os.path.exists(file):
        os.remove(file)

with open(NUMERICAL_RESULTS_FILE, "w") as fh:
    logger.info(f"Writing numerical results to {NUMERICAL_RESULTS_FILE}")
    fh.write("correct\tquestion\tvariation\texpected\tvalue\tanswer\n")
with open(TEXTUAL_RESULTS_FILE, "w") as fh:
    logger.info(f"Writing textual results to {TEXTUAL_RESULTS_FILE}")
    fh.write(
        "question\tvariation\texpected\tanswer\tfaithfulness_score\t"
        "faithfulness_justification\tcompleteness_score\tcompleteness_justification\t"
        "conciseness_score\tconciseness_justification\n"
    )

with open("unicef_geospatial/utils/prompts.yaml", "r") as f:
    prompts = yaml.safe_load(f)

extract_number_prompt = prompts["extract_number_prompt"]
score_textual_answer_prompt = prompts["score_textual_answer_prompt"]


@pytest.mark.parametrize("question,expected,response_type,variation", benchmark_list)
@pytest.mark.asyncio
async def test_agent_question(question, expected, response_type, variation):
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
    if response_type == "numerical":
        evaluate_numerical_answer(
            "r_" + trace_id, question, expected, final_answer, variation
        )
    else:
        evaluate_textual_answer(
            "r_" + trace_id, question, expected, final_answer, variation
        )


def evaluate_numerical_answer(
    trace_id: str, question: str, expected: int, answer: str, variation: str
) -> bool:
    numerical_value = extract_number_from_response(
        question, answer, extract_number_prompt
    )
    if numerical_value is None:
        is_correct = False
    else:
        tolerance = expected * 0.01
        is_correct = abs(numerical_value - expected) <= tolerance
    with open(NUMERICAL_RESULTS_FILE, "a+") as fh:
        answer = answer.replace("\n", "||")
        fh.write(
            f"{is_correct}\t{question}\t{variation}\t{expected}\t{numerical_value}\t{answer}\n"
        )

    langfuse.score(
        trace_id=trace_id,
        name="answer_correctness",
        value="correct" if is_correct else "incorrect",
        comment=f"Expected: {expected}, Got: {answer}",
    )

    assert (
        is_correct
    ), f"Answer doesn't match expected value for question: {question}\n\
        Expected: {expected}\nGot: {numerical_value}\n\
        Full answer: {answer}"


def evaluate_textual_answer(
    trace_id: str, question: str, expected: str, answer: str, variation: str
) -> bool:
    result = score_textual_answer(
        question, expected, answer, score_textual_answer_prompt
    )

    with open(TEXTUAL_RESULTS_FILE, "a+") as fh:
        fh.write(
            f"{question}\t{variation}\t{expected}\t{answer}\t"
            f"{result.faithfulness.result}\t{result.faithfulness.justification}\t"
            f"{result.completeness.result}\t{result.completeness.justification}\t"
            f"{result.conciseness.result}\t{result.conciseness.justification}\n"
        )

    langfuse.score(
        trace_id=trace_id,
        name="faithfulness",
        value=result.faithfulness.result,
        comment=result.faithfulness.justification,
    )

    langfuse.score(
        trace_id=trace_id,
        name="completeness",
        value=result.completeness.result,
        comment=result.completeness.justification,
    )

    langfuse.score(
        trace_id=trace_id,
        name="conciseness",
        value=result.conciseness.result,
        comment=result.conciseness.justification,
    )

    assert True
