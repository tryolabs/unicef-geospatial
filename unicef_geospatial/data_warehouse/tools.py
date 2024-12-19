from langchain.tools import tool

from unicef_geospatial.data_warehouse.unicef_api import (
    get_available_dataflows,
    get_data,
)
from unicef_geospatial.utils.country import get_country_code


@tool
def get_all_indicators_for_dataflow(
    dataflow_id: str,
    ref_areas: list[str] | None = None,
) -> list[str]:
    """Get all indicators for the dataflow.

    Args:
        dataflow_id: Dataflow ID to get indicators for
        ref_areas: Optional list of country names, codes or ISO-3 codes to filter by.
                  If None, returns indicators for all countries.

    Returns:
        list[str]: List of unique indicator codes available for the specified countries.
    """
    if ref_areas is not None:
        ref_areas = [get_country_code(area) for area in ref_areas]
    data = get_data(dataflow_id, ref_areas=ref_areas)
    return data["INDICATOR"].unique().tolist()


@tool
def get_available_dataflows_info() -> str:
    """Get the available dataflows and their descriptions.

    Returns:
        str: Information on all available dataflows.
    """
    return get_available_dataflows()


@tool
def get_data_for_dataflow(
    dataflow_id: str,
    ref_areas: str,
    indicators: str,
) -> str:
    """Get data for a specific dataflow.

    Args:
        dataflow_id: Dataflow ID to get data for
        ref_areas: Optional list of country names, codes or ISO-3 codes to filter by.
                  If None, returns data for all countries.
        indicators: Optional list of indicator codes to retrieve. If None, returns data for all indicators.

    Returns:
        str: The observed value for the specified country and indicator

    Raises:
        IndexError: If no data is found for the given country and indicator
    """
    ref_areas = get_country_code(ref_areas)
    data = get_data(dataflow_id, ref_areas=[ref_areas], indicators=[indicators])
    return data["OBS_VALUE"].to_numpy()[0]
