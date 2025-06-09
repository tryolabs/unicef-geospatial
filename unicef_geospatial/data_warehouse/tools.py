from logging import getLogger

from data_warehouse.unicef_api import (
    get_available_dataflows,
    get_data,
    get_indicators_information,
)
from geospatial.demographic import get_country_code

logger = getLogger(__name__)


def get_all_indicators_for_dataflow(
    dataflow_id: str,
) -> dict[str, str | dict[str, str]]:
    """Get all indicators for the dataflow.

    Args:
        dataflow_id: Dataflow ID to get indicators for

    Returns:
        dict[str, str | dict[str, str]]: Dictionary containing indicators info and input arguments.
    """
    logger.info(f"Getting all indicators for dataflow {dataflow_id}")
    indicators_info = get_indicators_information(dataflow_id)
    return {
        "indicators_info": indicators_info,
        "input_arguments": {"dataflow_id": dataflow_id},
    }


def get_available_dataflows_info() -> dict[str, str | dict]:
    """Get the available dataflows and their descriptions.

    Returns:
        dict[str, str | dict]: Dictionary containing available dataflows and input arguments.
    """
    logger.info("Getting available dataflows")
    return {
        "available_dataflows": get_available_dataflows(),
        "input_arguments": {},
    }


def get_data_for_dataflow(
    dataflow_id: str,
    ref_areas: str,
    indicators: str,
    year: int | None = None,
) -> dict[str, str | dict[str, str | list[str] | int | None]]:
    """Get data for a specific dataflow.

    Returns all available data that matches the criteria.
    If the year is not found, it will return all data for that country and indicator.

    Args:
        dataflow_id: Dataflow ID to get data for
        ref_areas: Comma-separated string of country names, codes or ISO-3 codes to filter by.
        indicators: Comma-separated string of indicator codes to retrieve.
        year: The year of the data to retrieve.

    Returns:
        dict[str, str | dict[str, str | list[str] | int | None]]: Dictionary containing data and input arguments.

    Raises:
        IndexError: If no data is found for the given country and indicator
    """
    logger.info(f"Getting data for dataflow {dataflow_id}")
    ref_areas_list = ref_areas.split(",")
    ref_areas_codes = [get_country_code(area) for area in ref_areas_list]
    data = get_data(
        dataflow_id, ref_areas=ref_areas_codes, indicators=indicators.split(",")
    )
    if year is not None and str(year) in data["TIME_PERIOD"].unique():
        data = data[data["TIME_PERIOD"] == str(year)]
    return {
        "data": str(data),
        "input_arguments": {
            "dataflow_id": dataflow_id,
            "ref_areas": ref_areas_codes,
            "indicators": indicators,
            "year": year,
        },
    }
