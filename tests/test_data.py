import os
from typing import List

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatLiteLLM
from pydantic import BaseModel


class Answer(BaseModel):
    "Numerical answer of the question"

    value: int | None


def extract_number_from_response(question: str, answer: str) -> int | None:
    """Extract numerical answer from response using an LLM.

    Args:
        question: The question
        answer: The answer text

    Returns:
        The extracted number or None if no number is found
    """
    parser = PydanticOutputParser(pydantic_object=Answer)

    prompt = ChatPromptTemplate.from_template(
        """
    You are tasked with extracting the numerical answer (or None).
    For this you will be provided a question and the provided answer.
    
    === Question ===
    {question}
    === Answer ====
    {answer}
    
    Extract the number that answers the question, or return None if no number is found.
    {format_instructions}
    """
    )

    model = ChatLiteLLM(model=os.getenv("MODEL_NAME", "gpt-4o-mini"))

    chain = prompt | model | parser

    result = chain.invoke(
        {
            "question": question,
            "answer": answer,
            "format_instructions": parser.get_format_instructions(),
        }
    )

    return result.value


class BechmarkQuestion(BaseModel):
    question: str
    variations: List[str]
    answer: int


class Benchmark(BaseModel):
    questions: List[BechmarkQuestion]


def benchmark_question_to_tuple(bq: BechmarkQuestion) -> tuple:
    result = []
    for q in bq.variations + [bq.question]:
        instance = (q, bq.answer, bq.question)
        result.append(instance)

    return result


def benchmark_to_list(benchmark: Benchmark) -> list:
    result = []
    for bq in benchmark.questions:
        instance = benchmark_question_to_tuple(bq)
        result.extend(instance)
    return result


#################
###### Questions
#################

benchmark_questions = []

benchmark_questions.append(
    BechmarkQuestion(
        question="How many children were exposed to costal floods in Colombia",
        answer=22714,
        variations=[
            "How many children were affected by costal floods in Colombia?",
            "children impacted by costal floods in Colombia",
        ],
    )
)

benchmark_questions.append(
    BechmarkQuestion(
        question="How many children were exposed to costal floods in Angola",
        answer=6909,
        variations=[
            "How many children were affected by costal floods in Angola?",
            "children impacted by costal floods in Angola",
        ],
    )
)

benchmark_questions.append(
    BechmarkQuestion(
        question="How many children were exposed to costal floods in China",
        answer=11392856,
        variations=[
            "How many children were affected by costal floods in China?",
            "children impacted by costal floods in China",
        ],
    )
)

benchmark = Benchmark(questions=benchmark_questions)
benchmark_list = benchmark_to_list(benchmark)
