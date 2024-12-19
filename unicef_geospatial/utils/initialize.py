from typing import Callable

import ee
from geospatial.heatwaves.tools import (
    get_heatwave_metric_for_admin_level_1,
    get_heatwave_metric_for_country,
)
from geospatial.rainfall.tools import get_precipitation_for_country
from langchain.chat_models.base import BaseChatModel
from langchain_cohere import ChatCohere

from unicef_geospatial.data_warehouse.tools import (
    get_all_indicators_for_dataflow,
    get_available_dataflows_info,
    get_data_for_dataflow,
)


def initialize_earth_engine(project: str) -> None:
    """Initialize the Earth Engine API."""
    ee.Authenticate()
    ee.Initialize(project=project)


def get_llm(temperature: float) -> BaseChatModel:
    """Get the LLM model."""
    return ChatCohere(temperature=temperature)


def get_tools() -> list[Callable]:
    """Get the tools."""
    return [
        get_heatwave_metric_for_country,
        get_heatwave_metric_for_admin_level_1,
        get_precipitation_for_country,
        get_all_indicators_for_dataflow,
        get_available_dataflows_info,
        get_data_for_dataflow,
    ]
