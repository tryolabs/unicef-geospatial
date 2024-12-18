from langchain.tools import tool

from unicef_geospatial.data_warehouse.unicef_api import get_data
from unicef_geospatial.utils.country import get_country_code


@tool
def get_all_indicators_for_climate_risk_index(
    ref_areas: list[str] | None = None,
) -> list[str]:
    """Get all indicators for the Climate Risk Index dataflow.

    Args:
        ref_areas: Optional list of country names, codes or ISO-3 codes to filter by.
                  If None, returns indicators for all countries.

    Returns:
        list[str]: List of unique indicator codes available for the specified countries.
    """
    if ref_areas is not None:
        ref_areas = [get_country_code(area) for area in ref_areas]
    data = get_data("CCRI", ref_areas=ref_areas)
    return data["INDICATOR"].unique().tolist()


@tool
def get_climate_risk_index_data(country: str, indicator: str) -> str:
    """Get climate risk index data for a specific country and indicator.

    Args:
        country: Country name, code or ISO-3 code to get data for
        indicator: Indicator code to retrieve (e.g. 'CCRI_WATER_SCARCITY')

    Returns:
        str: The observed value for the specified country and indicator

    Raises:
        IndexError: If no data is found for the given country and indicator
    """
    country_code = get_country_code(country)
    data = get_data("CCRI", ref_areas=[country_code], indicators=[indicator])
    return data["OBS_VALUE"].to_numpy()[0]
