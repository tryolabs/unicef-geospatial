import ee
from ee.filter import Filter
from ee.imagecollection import ImageCollection
from ee.reducer import Reducer
from langchain.tools import tool
from logging_config import get_logger
from utils.constants import DEMOGRAPHIC_BAND, DEMOGRAPHIC_DATASET, PATH_TO_MAP
from utils.types import AGE_GROUPS, SEXES

from unicef_geospatial.geospatial.geo_operations import image_to_html


@tool
def get_population_in_zone(
    path_to_vector_data: str,
    age_group: AGE_GROUPS = "Total Population",
    sex: SEXES = "b",
) -> dict[str, float | str]:
    """Calculate population count within a specified geographic zone.

    Args:
        path_to_vector_data: Path to the geometry to clip the demographic data
        age_group: Age group to analyze.
        sex: Sex to analyze.

    Returns:
        dict[str, float | str]: A dictionary containing:
            - population (float): Population count in millions
            - path_to_map (str): Path to the generated map file
    """

    try:
        # Convert the dictionary to FeatureCollection
        logger = get_logger(__name__)
        with open(path_to_vector_data, "r") as f:
            logger.info(f"Going to load vector data from {path_to_vector_data}")
            json_value = eval(f.read())
            zone_vector = ee.deserializer.fromJSON(json_value)

        zone_vector = zone_vector.getInfo()
        zone_vector = ee.FeatureCollection(zone_vector)
    except Exception as e:
        logger.error(f"Error in vector conversion: {str(e)}")
        raise e

    demographic = ImageCollection(DEMOGRAPHIC_DATASET)
    demographic_image = (
        demographic.filter(Filter.eq("Age_Group", age_group))
        .filter(Filter.eq("Sex", sex))
        .first()
    )
    if demographic_image is None:
        logger.error("No demographic image found for the given age group and sex")
        raise ValueError("No demographic image found for the given age group and sex")

    scale = demographic_image.projection().nominalScale().getInfo()

    masked_demographic = demographic_image.clip(zone_vector)

    raster_vis = {
        "max": 1000.0,
        "palette": [
            "ffffe7",
            "86a192",
            "509791",
            "307296",
            "2c4484",
            "000066",
        ],
        "min": 0.0,
    }

    html = image_to_html(masked_demographic, name="Population", vis_params=raster_vis)

    with open(PATH_TO_MAP, "w") as f:
        f.write(html)

    result = masked_demographic.reduceRegion(
        reducer=Reducer.sum(),
        geometry=zone_vector,
        scale=scale,
        maxPixels=1e9,
    ).getInfo()

    if result is None:
        logger.error("No result found for the given zone vectors")
        raise ValueError("No result found for the given zone vectors")

    population_count = result.get(DEMOGRAPHIC_BAND, 0)
    population_millions = round(population_count / 1_000_000, 2)

    return {"population": population_millions, "path_to_map": PATH_TO_MAP}


@tool
def get_country_map(country: str) -> str:
    """Returns an HTML string containing an interactive map centered on the specified country.

    Args:
        country (str): The name of the country to display on the map. Must match the country
            names in the USDOS/LSIB_SIMPLE/2017 Earth Engine dataset.

    Returns:
        str: HTML string containing the interactive map with the country boundaries highlighted.
    """
    countries_boundries = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
    country_boundries = countries_boundries.filter(ee.Filter.eq("country_na", country))

    html = image_to_html(
        image=country_boundries, name=f"{country} Boundaries", center=True
    )

    with open(PATH_TO_MAP, "w") as f:
        f.write(html)

    return {"path_to_map": PATH_TO_MAP}
