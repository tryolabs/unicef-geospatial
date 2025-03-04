import ee
from geospatial.geo_operations import load_vector_data
from langchain.tools import tool
from utils.constants import RAINFALL_DATASET
from utils.types import REDUCERS

INITIAL_YEAR = 1979
LAST_INDEX = 12 * (2020 - INITIAL_YEAR) + 6


@tool
def get_precipitation_for_zone(
    year: int,
    month: int,
    path_to_vector_data: str,
    reducer: REDUCERS = "mean",
) -> float:
    """Get the total precipitation for a specific zone and month (in mm).

    Args:
        year: The year of the precipitation
        month: The month of the precipitation
        path_to_vector_data: Path to the geometry to clip the precipitation data
        reducer: The reducer to use ('mean', 'max', 'min', etc). Defaults to 'mean'

    Returns:
        The value of the precipitation for the specified area and month (in mm)
    """
    rainfall_image = get_rainfall_image(year, month)

    zone_vector = load_vector_data(path_to_vector_data)

    rainfall_image = rainfall_image.clip(zone_vector)

    stats = rainfall_image.reduceRegion(
        reducer=getattr(ee.Reducer, reducer)(),
        geometry=zone_vector.geometry(),
        scale=1000,
        maxPixels=1e13,
    )
    return {
        "value": round(stats.getInfo()["total_precipitation"] * 1000, 3),
        "input_arguments": {
            "year": year,
            "month": month,
            "path_to_vector_data": path_to_vector_data,
            "reducer": reducer,
        },
    }


def get_rainfall_image(year: int, month: int) -> ee.Image:
    index = (year - INITIAL_YEAR) * 12 + month - 1
    if index > LAST_INDEX or index < 0:
        error_msg = f"Index {index} is out of bounds"
        raise ValueError(error_msg)

    rainfall_dataset = ee.ImageCollection(RAINFALL_DATASET)
    rainfall_list = rainfall_dataset.toList(rainfall_dataset.size())
    rainfall_image = ee.Image(rainfall_list.get(index))
    return rainfall_image
