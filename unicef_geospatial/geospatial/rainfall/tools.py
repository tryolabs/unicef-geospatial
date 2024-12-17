# %%
import ee
from langchain.tools import tool
from utils.constants import COUNTRY_BOUNDRIES_DATASET, RAINFALL_DATASET
from utils.types import REDUCERS

INITIAL_YEAR = 1979
LAST_INDEX = 12 * (2020 - INITIAL_YEAR) + 6


@tool
def get_precipitation_for_country(
    year: int, month: int, country: str, reducer: REDUCERS = "mean"
) -> float:
    """Get the total precipitation for a specific country and month (in mm).

    Args:
        year: The year of the precipitation
        month: The month of the precipitation
        country: Name of the country
        reducer: The reducer to use ('mean', 'max', 'min', etc). Defaults to 'mean'

    Returns:
        The value of the precipitation for the specified country and month (in mm)
    """
    rainfall_image = get_rainfall_image(year, month)
    countries_boundries = ee.FeatureCollection(COUNTRY_BOUNDRIES_DATASET)
    countries_boundries = countries_boundries.filter(
        ee.Filter.eq("country_na", country)
    )
    rainfall_image = rainfall_image.clip(countries_boundries)
    stats = rainfall_image.reduceRegion(
        reducer=getattr(ee.Reducer, reducer)(),
        geometry=countries_boundries.geometry(),
        scale=1000,
        maxPixels=1e13,
    )
    return round(stats.getInfo()["total_precipitation"] * 1000, 3)


def get_rainfall_image(year: int, month: int) -> ee.Image:
    index = (year - INITIAL_YEAR) * 12 + month - 1
    if index > LAST_INDEX or index < 0:
        error_msg = f"Index {index} is out of bounds"
        raise ValueError(error_msg)

    rainfall_dataset = ee.ImageCollection(RAINFALL_DATASET)
    rainfall_list = rainfall_dataset.toList(rainfall_dataset.size())
    rainfall_image = ee.Image(rainfall_list.get(index))
    return rainfall_image
