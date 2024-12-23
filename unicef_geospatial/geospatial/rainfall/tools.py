import ee
from langchain.tools import tool
from utils.constants import RAINFALL_DATASET
from utils.country import filter_dataset_by_area, standarize_country_name
from utils.types import AREA_TYPES, REDUCERS

INITIAL_YEAR = 1979
LAST_INDEX = 12 * (2020 - INITIAL_YEAR) + 6


@tool
def get_precipitation_for_area(
    year: int,
    month: int,
    area_name: str,
    area_type: AREA_TYPES = "country",
    reducer: REDUCERS = "mean",
) -> float:
    """Get the total precipitation for a specific country and month (in mm).

    Args:
        year: The year of the precipitation
        month: The month of the precipitation
        area_name: Name of the area (country or admin level 1)
        area_type: Type of area - either 'country' for counetries
            or 'admin1' for admin level 1 like states or provinces.
            Defaults to 'country'
        reducer: The reducer to use ('mean', 'max', 'min', etc). Defaults to 'mean'

    Returns:
        The value of the precipitation for the specified area and month (in mm)
    """
    rainfall_image = get_rainfall_image(year, month)
    if area_type == "country":
        area_name = standarize_country_name(area_name)
    rainfall_area_image, area_boundry = filter_dataset_by_area(
        rainfall_image, area_name, area_type
    )
    stats = rainfall_area_image.reduceRegion(
        reducer=getattr(ee.Reducer, reducer)(),
        geometry=area_boundry.geometry(),
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
