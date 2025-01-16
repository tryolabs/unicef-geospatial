from ee.featurecollection import FeatureCollection
from ee.filter import Filter
from ee.imagecollection import ImageCollection
from ee.reducer import Reducer
from langchain.tools import tool
from utils.constants import DEMOGRAPHIC_BAND, DEMOGRAPHIC_DATASET
from utils.types import AGE_GROUPS, SEXES


@tool
def get_population_in_zone(
    zone_vector: FeatureCollection,
    age_group: AGE_GROUPS = "Total Population",
    sex: SEXES = "b",
) -> float:
    """Calculate population count within a specified geographic zone.

    Args:
        age_group: Age group to analyze.
        sex: Sex to analyze.
        zone_vector: Earth Engine FeatureCollection defining the geographic zone to analyze

    Returns:
        float: Total population count in the zone (in millions)
    """
    demographic = ImageCollection(DEMOGRAPHIC_DATASET)
    demographic_image = (
        demographic.filter(Filter.eq("Age_Group", age_group))
        .filter(Filter.eq("Sex", sex))
        .first()
    )
    if demographic_image is None:
        raise ValueError("No demographic image found for the given age group and sex")

    scale = demographic_image.projection().nominalScale().getInfo()

    masked_demographic = demographic_image.clip(zone_vector)

    result = masked_demographic.reduceRegion(
        reducer=Reducer.sum(),
        geometry=zone_vector,
        scale=scale,
        maxPixels=1e14,
    ).getInfo()

    if result is None:
        error = "No result found for the given zone vectors"
        raise ValueError(error)

    population_count = result.get(DEMOGRAPHIC_BAND, 0)
    population_millions = round(population_count / 1_000_000, 2)

    return population_millions
