from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel


class Message(BaseModel):
    content: str
    role: Literal["user", "assistant"]
    trace_id: str


class ReturnChunk(BaseModel):
    trace_id: str
    response: str = ""
    tool_call: str = ""
    is_html: bool = False
    html_content: str = ""
    is_finished: bool = False


class Chat(BaseModel):
    chat_messages: list[Message]
    session_id: str


class DatasetMetadata(BaseModel):
    image_filename: str
    asset_id: str
    description: str
    source_name: str
    source_url: str
    mosaic: bool = False
    threshold: float | None = None
    input_arguments: dict[str, Any] = {}


class ALL_DATASETS(str, Enum):
    RIVER_FLOOD = "river_flood"
    COASTAL_FLOOD = "coastal_flood"
    CHILDREN_POPULATION = "children_population"
    TROPICAL_STORM = "tropical_storm"
    AGRICULTURAL_DROUGHT = "agricultural_drought"
    DROUGHT_SPEI = "drought_spei"
    DROUGHT_SPI = "drought_spi"
    HEATWAVE_FREQUENCY = "heatwave_frequency"
    HEATWAVE_DURATION = "heatwave_duration"
    HEATWAVE_SEVERITY = "heatwave_severity"
    EXTREME_HEAT = "extreme_heat"
    FIRE = "fire"
    FIRE_FRP = "fire_frp"
    SAND_DUST_STORM = "sand_dust_storm"
    AIR_POLLUTION = "air_pollution"
    PLASMODIUM_VIVAX = "plasmodium_vivax"
    PLASMODIUM_FALCIPARUM = "plasmodium_falciparum"


METRICS = Literal["frequency", "duration", "severity", "extreme_high_temp"]
DECADES = Literal["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
REDUCERS = Literal["mean", "max", "min", "sum", "median", "std"]
AREA_TYPES = Literal["country", "admin1"]
