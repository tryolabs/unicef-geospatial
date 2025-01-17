import ee
from ee.filter import Filter
from ee.imagecollection import ImageCollection
from ee.reducer import Reducer
from langchain.tools import tool
from logging_config import get_logger
from utils.constants import DEMOGRAPHIC_BAND, DEMOGRAPHIC_DATASET
from utils.types import AGE_GROUPS, SEXES


@tool
def get_population_in_zone(
    path_to_vector_data: str,
    age_group: AGE_GROUPS = "Total Population",
    sex: SEXES = "b",
) -> float:
    """Calculate population count within a specified geographic zone.

    Args:
        path_to_vector_data: Path to the geometry to clip the demographic data
        age_group: Age group to analyze.
        sex: Sex to analyze.

    Returns:
        float: Total population count in the zone (in millions)
    """
    # Convert the dictionary to FeatureCollection

    try:
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

    return population_millions
