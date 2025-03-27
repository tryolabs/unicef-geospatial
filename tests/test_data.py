from typing import List
from pydantic import BaseModel
from llama_index.program.openai import OpenAIPydanticProgram

class Answer(BaseModel):
    "Numerical answer of the question"
    value: int | None

def extract_number_from_response(q: str, a: str):

    prompt_template_str = """\
    You are tasked with extracting the numerical answer (or None).\
    For this you will be provided a question and the provided answer\
    === Question ===
    {question}
    === Answer ====
    {answer}
    """
    program = OpenAIPydanticProgram.from_defaults(
        output_cls=Answer, prompt_template_str=prompt_template_str, verbose=True
    )
    output = program(question=q, answer=a)
    return output.value


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
            "children impacted by costal floods in Colombia"
        ]
    )
)

benchmark_questions.append(
    BechmarkQuestion(
        question="How many children were exposed to costal floods in Angola",
        answer=6909,
        variations=[
            "How many children were affected by costal floods in Angola?",
            "children impacted by costal floods in Angola"
        ]
    )
)

benchmark_questions.append(
    BechmarkQuestion(
        question="How many children were exposed to costal floods in China",
        answer=11392856,
        variations=[
            "How many children were affected by costal floods in China?",
            "children impacted by costal floods in China"
        ]
    )
)

benchmark = Benchmark(questions=benchmark_questions)
benchmark_list = benchmark_to_list(benchmark)


