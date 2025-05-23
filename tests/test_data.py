import os

from llama_index.core.program import LLMTextCompletionProgram
from llama_index.llms.litellm import LiteLLM
from pydantic import BaseModel

from tests.questions_datawarehouse import benchmark_questions as warehouse_questions
from tests.questions_gee import benchmark_questions as gee_questions
from tests.questions_techincal_doc import benchmark_questions as technical_doc_questions
from tests.types import BechmarkQuestion, Benchmark


class NumericalAnswer(BaseModel):
    "Numerical answer of the question"

    value: int | None


class TextualAnswer(BaseModel):
    "Textual answer of the question"

    result: int
    justification: str


class TextualEvaluation(BaseModel):
    "Evaluation of the answer"

    faithfulness: TextualAnswer
    completeness: TextualAnswer
    conciseness: TextualAnswer


def extract_number_from_response(question: str, answer: str, prompt: str) -> int | None:
    """Extract numerical answer from response using an LLM.

    Args:
        question: The question
        answer: The answer text

    Returns:
        The extracted number or None if no number is found
    """
    model = LiteLLM(model=os.getenv("MODEL_NAME", "gpt-4o-mini"))

    program = LLMTextCompletionProgram.from_defaults(
        llm=model,
        prompt_template_str=prompt,
        output_cls=NumericalAnswer,
    )

    result = program(question=question, answer=answer)

    return result.value


def score_textual_answer(
    question: str, ground_truth: str, candidate_answer: str, prompt: str
) -> TextualEvaluation:
    """Evaluate the quality of a textual answer against a ground truth.

    Args:
        question: The original question
        ground_truth: The ground truth answer (considered ideal and accurate)
        candidate_answer: The answer to evaluate

    Returns:
        A dictionary containing evaluation scores and justifications for faithfulness,
        completeness, and conciseness on a scale of 1-5
    """
    model = LiteLLM(model=os.getenv("MODEL_NAME", "gpt-4o"))

    program = LLMTextCompletionProgram.from_defaults(
        llm=model,
        prompt_template_str=prompt,
        output_cls=TextualEvaluation,
    )

    result = program(
        question=question,
        ground_truth=ground_truth,
        candidate_answer=candidate_answer,
    )

    return result


def benchmark_question_to_tuple(bq: BechmarkQuestion) -> tuple:
    result = []
    questions = [bq.question]
    if bq.variations:
        questions += bq.variations
    for q in questions:
        instance = (q, bq.answer, bq.response_type, bq.question)
        result.append(instance)

    return result


def benchmark_to_list(benchmark: Benchmark) -> list:
    result = []
    for bq in benchmark.questions:
        instance = benchmark_question_to_tuple(bq)
        result.extend(instance)
    return result


benchmark_questions = [
    *technical_doc_questions,
    *gee_questions,
    *warehouse_questions,
]

benchmark = Benchmark(questions=benchmark_questions)
benchmark_list = benchmark_to_list(benchmark)
