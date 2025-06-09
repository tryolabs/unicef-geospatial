import json
from functools import partial
from pathlib import Path
from typing import Callable

import ee
from data_warehouse.tools import (
    get_all_indicators_for_dataflow,
    get_available_dataflows_info,
    get_data_for_dataflow,
)
from geospatial.demographic import get_zone_of_area
from geospatial.geo_operations import (
    build_map,
    filter_image_by_threshold,
    get_dataset_image_and_metadata,
    intersect_binary_images,
    intersect_feature_collections,
    mask_image,
    merge_feature_collections,
    reduce_image,
    union_binary_images,
)
from llama_index.core.tools import FunctionTool
from technical_doc import get_ccri_metadata


def initialize_earth_engine(path_to_ee_auth: str) -> None:
    """Initialize the Earth Engine API."""
    key_path = Path(path_to_ee_auth)
    key_file = key_path.read_text()
    key_dict = json.loads(key_file)
    email = key_dict["client_email"]

    auth = ee.ServiceAccountCredentials(email=email, key_data=key_file)
    ee.Initialize(auth)


def get_tools(temp_dir: str = "") -> list[Callable]:
    """Get the tools."""
    tools = [
        # data_warehouse tools
        get_available_dataflows_info,
        get_all_indicators_for_dataflow,
        get_data_for_dataflow,
        # geospatial operation tools
        filter_image_by_threshold,
        mask_image,
        intersect_feature_collections,
        merge_feature_collections,
        reduce_image,
        intersect_binary_images,
        union_binary_images,
        # geospatial querying tools
        get_zone_of_area,
        get_dataset_image_and_metadata,
        get_ccri_metadata,
        build_map,
    ]

    # Create tools with bound parameters for temp_dir
    tool_instances = []
    for tool in tools:
        if "temp_dir" in tool.__code__.co_varnames:
            new_tool = bound_tool(tool, temp_dir)
            tool_instances.append(new_tool)

        else:
            tool_instances.append(tool)

    return tool_instances


def bound_tool(tool: Callable, temp_dir: str = "") -> Callable:
    bound_func = partial(tool, temp_dir=temp_dir)

    # Create a new FunctionTool with the bound function
    new_tool = FunctionTool.from_defaults(
        name=tool.__name__,
        description=tool.__doc__ or "",
        fn=bound_func,
    )

    return new_tool
