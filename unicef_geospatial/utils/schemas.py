from enum import Enum
from typing import Any, Literal

import yaml
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
    color_palette: list[str] = []


def load_all_datasets_enum() -> Enum:
    """Load dataset names from the YAML metadata file and create enum values"""
    from utils.constants import PATH_TO_HAZARDS_METADATA

    try:
        with open(PATH_TO_HAZARDS_METADATA, "r") as file:
            data = yaml.safe_load(file)
            if data and "datasets" in data:
                dataset_names = list(data["datasets"].keys())
                ALL_DATASETS = Enum(
                    "ALL_DATASETS",
                    {name.upper(): name for name in dataset_names},
                    type=str,
                )

                return ALL_DATASETS
    except (FileNotFoundError, yaml.YAMLError):
        raise ValueError("Failed to load dataset metadata")


REDUCERS = Literal["mean", "max", "min", "sum", "median", "std"]
AREA_TYPES = Literal["country", "admin1"]
