from typing import List, Literal

from pydantic import BaseModel

RESPONSE_TYPE = Literal["numerical", "textual"]


class BechmarkQuestion(BaseModel):
    question: str
    variations: List[str] | None
    response_type: RESPONSE_TYPE
    answer: int | str


class Benchmark(BaseModel):
    questions: List[BechmarkQuestion]
