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
    If the answer includes something like "There is none people exposed to this hazard", return 0.
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

# DataWarehouse Questions

benchmark_questions.append(
    BechmarkQuestion(
        question="What's the percentage of births without a birth weight registered in Nigeria?",
        answer=77,
        variations=[
            "percentage of births without a birth weight registered in Nigeria",
        ],
    )
)
benchmark_questions.append(
    BechmarkQuestion(
        question="What was the percentage of children vaccinated for tuberculosis in Ethiopia in 2020?",
        answer=70,
        variations=[
            "percentage of children vaccinated for tuberculosis in Ethiopia in 2020",
        ],
    )
)

# Multi-Hazard Questions
data_single_hazard = {
    "agricultural drought": {
        "Angola": 4099009,
        "Nicaragua": 878626,
        "Uruguay": 233589,
        "Colombia": 3149198,
    },
    "air pollution": {
        "Angola": 16338870,
        "Nicaragua": 1976847,
        "Uruguay": 604115,
        "Colombia": 11212840,
    },
    "coastal floods": {
        "Angola": 6909,
        "Nicaragua": 3977,
        "Uruguay": 910,
        "Colombia": 22714,
    },
    "drought SPEI": {
        "Angola": 573838,
        "Nicaragua": 6326,
        "Uruguay": 119691,
        "Colombia": 2361523,
    },
    "drought SPI": {
        "Angola": 114626,
        "Nicaragua": 6326,
        "Uruguay": 115915,
        "Colombia": 1438632,
    },
    "extreme heat": {
        "Angola": 2360001,
        "Nicaragua": 574883,
        "Uruguay": 0,
        "Colombia": 1272004,
    },
    "fire frequency": {
        "Angola": 5394005,
        "Nicaragua": 89740,
        "Uruguay": 120480,
        "Colombia": 157301,
    },
    "fire intensity": {
        "Angola": 1154385,
        "Nicaragua": 72040,
        "Uruguay": 60119,
        "Colombia": 589614,
    },
    "heatwave duration": {
        "Angola": 13274160,
        "Nicaragua": 1974811,
        "Uruguay": 0,
        "Colombia": 9452636,
    },
    "heatwave frequency": {
        "Angola": 13974860,
        "Nicaragua": 1971445,
        "Uruguay": 0,
        "Colombia": 10066570,
    },
    "heatwave severity": {
        "Angola": 0,
        "Nicaragua": 0,
        "Uruguay": 529360,
        "Colombia": 19277,
    },
    "pluvial floods": {
        "Angola": 8671705,
        "Nicaragua": 1178148,
        "Uruguay": 613335,
        "Colombia": 8158365,
    },
    "river floods": {
        "Angola": 714157,
        "Nicaragua": 38704,
        "Uruguay": 47840,
        "Colombia": 797908,
    },
    "sand and dust storms": {
        "Angola": 1027946,
        "Nicaragua": 43,
        "Uruguay": 88,
        "Colombia": 32659,
    },
    "tropical storms": {
        "Angola": 0,
        "Nicaragua": 2024094,
        "Uruguay": 0,
        "Colombia": 1748864,
    },
    "vectorborne malaria pv": {
        "Angola": 0,
        "Nicaragua": 441785,
        "Uruguay": 0,
        "Colombia": 6174789,
    },
    "vectorborne malaria pf": {
        "Angola": 15984150,
        "Nicaragua": 77840,
        "Uruguay": 0,
        "Colombia": 366051,
    },
}

data_multi_hazard = {
    # and river and coastal floods
    "river and coastal floods": {
        "Colombia": 12368,
        "Angola": 1293,
        "Nicaragua": 2039,
        "Uruguay": 807,
    },
    # or river or coastal floods
    "river or coastal floods": {
        "Colombia": 808254,
        "Angola": 719773,
        "Nicaragua": 40642,
        "Uruguay": 47943,
    },
    # and malaria
    "both kinds of malaria": {
        "Colombia": 366034,
        "Angola": 0,
        "Nicaragua": 44914,
        "Uruguay": 0,
    },
    # or malaria
    "any kind of malaria": {
        "Colombia": 6174806,
        "Angola": 15984153,
        "Nicaragua": 474711,
        "Uruguay": 0,
    },
    # and floods
    "all kinds of floods": {
        "Colombia": 12035,
        "Angola": 367,
        "Nicaragua": 1693,
        "Uruguay": 724,
    },
    # or floods
    "some kind of flood": {
        "Colombia": 8191207,
        "Angola": 8974501,
        "Nicaragua": 1190525,
        "Uruguay": 620872,
    },
}
# Iterate through data to create benchmark questions
# Combine single and multi-hazard data
# data = {**data_single_hazard, **data_multi_hazard}
data = data_multi_hazard
for hazard_name, countries in data.items():
    for country, value in countries.items():
        benchmark_questions.append(
            BechmarkQuestion(
                question=f"How many children were exposed to {hazard_name} in {country}",
                answer=value,
                variations=[
                    f"How many children were affected by {hazard_name} in {country}?",
                    f"children impacted by {hazard_name} in {country}",
                ],
            )
        )


benchmark = Benchmark(questions=benchmark_questions)
benchmark_list = benchmark_to_list(benchmark)
