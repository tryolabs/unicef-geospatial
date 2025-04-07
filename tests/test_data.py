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

# benchmark_questions.append(
#     BechmarkQuestion(
#         question="What's the percentage of births without a birth weight registered in Nigeria?",
#         answer=77,
#         variations=[
#             "percentage of births without a birth weight registered in Nigeria",
#         ],
#     )
# )
# benchmark_questions.append(
#     BechmarkQuestion(
#         question="What was the percentage of children vaccinated for tuberculosis in Ethiopia in 2020?",
#         answer=70,
#         variations=[
#             "percentage of children vaccinated for tuberculosis in Ethiopia in 2020",
#         ],
#     )
# )

data = {
    "river_floods": {
        "Angola": 714157,
        "Nicaragua": 38704,
        "Uruguay": 47840,
        "Colombia": 797908,
    },
    "coastal_floods": {
        "Angola": 6909,
        "Nicaragua": 3977,
        "Uruguay": 910,
        "Colombia": 22714,
    },
    "pluvial_floods": {
        "Angola": 8671705,
        "Nicaragua": 1178148,
        "Uruguay": 613335,
        "Colombia": 8158365,
    },
    "tropical_storms": {
        "Angola": 0,
        "Nicaragua": 2024094,
        "Uruguay": 0,
        "Colombia": 1748864,
    },
    "agricultural_drought": {
        "Angola": 40791,
        "Nicaragua": 0,
        "Uruguay": 0,
        "Colombia": 8077,
    },
    "fire": {
        "Angola": 5394005,
        "Nicaragua": 89740,
        "Uruguay": 120480,
        "Colombia": 157301,
    },
    "sand_dust_storm": {
        "Angola": 1027946,
        "Nicaragua": 43,
        "Uruguay": 88,
        "Colombia": 32659,
    },
    "air_pollution": {
        "Angola": 16338870,
        "Nicaragua": 1976847,
        "Uruguay": 604115,
        "Colombia": 11212840,
    },
    "vectorborne_malaria_pv": {
        "Angola": 0,
        "Nicaragua": 441785,
        "Uruguay": 0,
        "Colombia": 6174789,
    },
    "vectorborne_malaria_pf": {
        "Angola": 15984150,
        "Nicaragua": 77840,
        "Uruguay": 0,
        "Colombia": 366051,
    },
}

# Iterate through data to create benchmark questions
for hazard, countries in data.items():
    for country, value in countries.items():
        hazard_name = hazard.replace("_", " ")

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
