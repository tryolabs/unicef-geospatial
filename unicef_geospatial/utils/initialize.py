import json
from pathlib import Path
from typing import Callable

import ee
from data_warehouse.tools import (
    get_all_indicators_for_dataflow,
    get_available_dataflows_info,
    get_data_for_dataflow,
)
from geospatial.demographic import (
    get_country_map,
    get_population_in_zone,
    get_zone_of_area,
)
from geospatial.droughts import get_drought_zones
from geospatial.heatwaves import get_heatwave_metric_for_zone
from geospatial.rainfall import get_precipitation_for_zone


def initialize_earth_engine(path_to_ee_auth: str) -> None:
    """Initialize the Earth Engine API."""
    key_path = Path(path_to_ee_auth)
    key_file = key_path.read_text()
    key_dict = json.loads(key_file)
    email = key_dict["client_email"]

    auth = ee.ServiceAccountCredentials(email=email, key_data=key_file)
    ee.Authenticate()
    ee.Initialize(auth)


def get_tools() -> list[Callable]:
    """Get the tools."""
    return [
        get_heatwave_metric_for_zone,
        get_precipitation_for_zone,
        get_zone_of_area,
        get_all_indicators_for_dataflow,
        get_available_dataflows_info,
        get_data_for_dataflow,
        get_country_map,
        get_population_in_zone,
        get_drought_zones,
    ]
