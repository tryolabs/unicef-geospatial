from typing import Literal, Optional

from pydantic import BaseModel


class Message(BaseModel):
    content: str
    role: Literal["user", "assistant"]
    trace_id: str
    feedback_given: Optional[Literal[0, 1]] = None


class Chat(BaseModel):
    chat_messages: list[Message]
    session_id: str


METRICS = Literal["frequency", "duration", "severity", "extreme_high_temp"]
DECADES = Literal["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
REDUCERS = Literal["mean", "max", "min", "sum", "median", "std"]
AREA_TYPES = Literal["country", "admin1"]
AGE_GROUPS = Literal[
    "0-4",
    "0-14",
    "5-9",
    "10-14",
    "15-19",
    "15-49",
    "15-64",
    "20-24",
    "25-29",
    "30-34",
    "35-39",
    "40-44",
    "45-49",
    "50-54",
    "55-59",
    "60-64",
    "65-69",
    "70-74",
    "75-79",
    "80-84",
    "65-",
    "70-",
    "75-",
    "80-",
    "85-",
    "Total Population",
]
SEXES = Literal["m", "f", "b"]
MONTHS = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
DAYS = Literal[
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
]
