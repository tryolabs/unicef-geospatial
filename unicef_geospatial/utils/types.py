from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel


class Message(BaseModel):
    content: str
    role: Literal["user", "assistant"]
    trace_id: str


class ReturnChunk(BaseModel):
    response: str
    tool_call: str
    trace_id: str
    is_html: bool
    html_content: str
    is_finished: bool


class Chat(BaseModel):
    chat_messages: list[Message]
    session_id: str


class DatasetMetadata(BaseModel):
    path_to_image: str
    asset_id: str
    description: str
    mosaic: bool = False
    threshold: float | None = None
    greater_than: bool | None = None
    input_arguments: dict[str, Any] = {}


class ALL_DATASETS(str, Enum):
    RIVER_FLOOD = "river_flood"
    COASTAL_FLOOD = "coastal_flood"
    PLUVIAL_FLOOD = "pluvial_flood"
    CHILDREN_POPULATION = "children_population"
    TROPICAL_STORM = "tropical_storm"
    AGRICULTURAL_DROUGHT = "agricultural_drought"
    FIRE = "fire"
    SAND_DUST_STORM = "sand_dust_storm"
    AIR_POLLUTION = "air_pollution"


def cast_dataset_to_enum(dataset: str) -> ALL_DATASETS:
    return ALL_DATASETS(dataset)


METRICS = Literal["frequency", "duration", "severity", "extreme_high_temp"]
DECADES = Literal["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
REDUCERS = Literal["mean", "max", "min", "sum", "median", "std"]
AREA_TYPES = Literal["country", "admin1"]
