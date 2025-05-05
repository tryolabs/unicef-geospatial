from tests.types import BechmarkQuestion

benchmark_questions = []

# DataWarehouse Questions

benchmark_questions.append(
    BechmarkQuestion(
        question="What's the percentage of births without a birth weight registered in Nigeria?",
        answer=77,
        variations=[
            "percentage of births without a birth weight registered in Nigeria",
        ],
        response_type="numerical",
    )
)
benchmark_questions.append(
    BechmarkQuestion(
        question="What was the percentage of children vaccinated for tuberculosis in Ethiopia in 2020?",
        answer=70,
        variations=[
            "percentage of children vaccinated for tuberculosis in Ethiopia in 2020",
        ],
        response_type="numerical",
    )
)
