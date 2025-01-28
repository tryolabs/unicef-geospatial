import json
from pathlib import Path
from typing import Callable

import ee
from data_warehouse.tools import (
    get_all_indicators_for_dataflow,
    get_available_dataflows_info,
    get_data_for_dataflow,
)
from geospatial.demographic.tools import get_country_map, get_population_in_zone
from geospatial.droughts.tools import get_drought_zones
from geospatial.heatwaves.tools import get_heatwave_metric_for_area
from geospatial.rainfall.tools import get_precipitation_for_area


def initialize_earth_engine() -> None:
    """Initialize the Earth Engine API."""
    key_path = Path("ee_auth.json")
    key_file = key_path.read_text()
    key_dict = json.loads(key_file)
    email = key_dict["client_email"]
    auth = ee.ServiceAccountCredentials(email=email, key_data=key_file)
    ee.Authenticate()
    ee.Initialize(auth)


def get_tools() -> list[Callable]:
    """Get the tools."""
    return [
        get_heatwave_metric_for_area,
        get_precipitation_for_area,
        get_all_indicators_for_dataflow,
        get_available_dataflows_info,
        get_data_for_dataflow,
        get_country_map,
        get_population_in_zone,
        get_drought_zones,
    ]
