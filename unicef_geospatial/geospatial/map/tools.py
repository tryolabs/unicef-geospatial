import ee
import geemap.foliumap as geemap
from langchain.tools import tool


@tool
def get_country_map(country: str) -> str:
    """Returns an HTML string containing an interactive map centered on the specified country.

    Args:
        country (str): The name of the country to display on the map. Must match the country
            names in the USDOS/LSIB_SIMPLE/2017 Earth Engine dataset.

    Returns:
        str: HTML string containing the interactive map with the country boundaries highlighted.
    """
    country_boundries = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
    uruguay_boundries = country_boundries.filter(ee.Filter.eq("country_na", country))

    country_map = geemap.Map()
    country_map.center_object(uruguay_boundries)
    country_map.add_layer(uruguay_boundries, {}, f"{country} Boundaries")

    html = country_map.to_html()
    if html is None:
        error_msg = "Failed to generate map"
        raise ValueError(error_msg)
    return html
