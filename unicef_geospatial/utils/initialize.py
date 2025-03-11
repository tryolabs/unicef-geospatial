import json
from pathlib import Path
from typing import Callable

import ee
from data_warehouse.tools import (
    get_all_indicators_for_dataflow,
    get_available_dataflows_info,
    get_data_for_dataflow,
)
from geospatial.earth_engine import get_dataset_metadata
from geospatial.geo_operations import (
    build_map,
    filter_image_by_threshold,
    get_dataset_image_and_metadata,
    intersect_feature_collection,
    reduce_image,
)

# from geospatial.heatwaves import get_heatwave_image


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
        # get_heatwave_image,
        filter_image_by_threshold,
        get_all_indicators_for_dataflow,
        get_available_dataflows_info,
        get_data_for_dataflow,
        intersect_feature_collection,
        reduce_image,
        build_map,
        get_dataset_metadata,
        get_dataset_image_and_metadata,
    ]
