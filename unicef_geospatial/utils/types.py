from typing import Literal

METRICS = Literal["frequency", "duration", "severity", "extreme_high_temp"]
DECADES = Literal["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
REDUCERS = Literal["mean", "max", "min"]
AREA_TYPES = Literal["country", "admin1"]
AGE_GROUPS = Literal[
    "0,4",
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
