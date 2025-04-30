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
from geospatial.hazards_metadata import get_ccri_metadata
from geospatial.heatwaves import get_heatwave_image
from langchain.tools import StructuredTool


def initialize_earth_engine(path_to_ee_auth: str) -> None:
    """Initialize the Earth Engine API."""
    key_path = Path(path_to_ee_auth)
    key_file = key_path.read_text()
    key_dict = json.loads(key_file)
    email = key_dict["client_email"]

    auth = ee.ServiceAccountCredentials(email=email, key_data=key_file)
    ee.Authenticate()
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
        build_map,
        # geospatial querying tools
        get_heatwave_image,
        get_zone_of_area,
        get_dataset_image_and_metadata,
        get_ccri_metadata,
    ]

    # Create tools with bound parameters for temp_dir
    tool_instances = []
    for tool in tools:
        if hasattr(tool, "func") and "temp_dir" in tool.func.__code__.co_varnames:
            # This is a tool that needs temp_dir
            # We need to create a tool with temp_dir bound
            bound_func = partial(tool.func, temp_dir=temp_dir)

            # Create a new StructuredTool with the bound function
            # but all other attributes remain the same
            new_tool = StructuredTool(
                name=tool.name,
                description=tool.description,
                func=bound_func,
                args_schema=tool.args_schema,
                return_direct=(
                    tool.return_direct if hasattr(tool, "return_direct") else False
                ),
                coroutine=tool.coroutine if hasattr(tool, "coroutine") else None,
            )
            tool_instances.append(new_tool)
        else:
            tool_instances.append(tool)

    return tool_instances
