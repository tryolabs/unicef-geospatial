import json

import pycountry
from ee.featurecollection import FeatureCollection
from ee.filter import Filter
from ee.imagecollection import ImageCollection
from ee.reducer import Reducer
from geospatial.geo_operations import image_to_html, load_vector_data, save_html
from langchain.tools import tool
from logging_config import get_logger
from utils.constants import (
    ADMIN_LEVEL_1_BOUNDRIES_DATASET,
    COUNTRY_BOUNDRIES_DATASET,
    DEMOGRAPHIC_BAND,
    DEMOGRAPHIC_DATASET,
    PATH_TO_MAP,
)
from utils.types import AGE_GROUPS, AREA_TYPES, SEXES

PATH_TO_VECTOR_DATA = "unicef_geospatial/data/map_zones.json"


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
    logger = get_logger(__name__)
    zone_vector = load_vector_data(path_to_vector_data)

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
    countries_boundries = FeatureCollection("USDOS/LSIB_SIMPLE/2017")
    country_boundries = countries_boundries.filter(Filter.eq("country_na", country))

    html = image_to_html(
        image=country_boundries, name=f"{country} Boundaries", center=True
    )

    save_html(PATH_TO_MAP, html)

    return {"path_to_map": PATH_TO_MAP}


@tool
def get_zone_of_area(area_name: str, area_type: AREA_TYPES) -> str:
    """Get the zone boundary for a specified area and clip the dataset to it.

    Retrieves the boundary geometry for either a country or admin level 1 area and uses it
    to clip the input dataset. The boundary is also saved as a vector file.

    Args:
        area_name: Name of the area (country or admin level 1) to get boundary for
        area_type: Type of area - either 'country' or 'admin1'

    Returns:
        Path to the JSON file containing the vector boundary data

    Example:
        To get boundary data for France:
        >>> zone_path = get_zone_of_area(dataset, "France", "country")

        To get boundary data for California:
        >>> zone_path = get_zone_of_area(dataset, "California", "admin1")
    """
    if area_type == "country":
        countries_boundries = FeatureCollection(COUNTRY_BOUNDRIES_DATASET)
        area_boundry = countries_boundries.filter(Filter.eq("country_na", area_name))
    else:
        admin_level_1_boundries = FeatureCollection(ADMIN_LEVEL_1_BOUNDRIES_DATASET)
        area_boundry = admin_level_1_boundries.filter(Filter.eq("shapeName", area_name))

    area_boundry_serialized = area_boundry.serialize()

    with open(PATH_TO_VECTOR_DATA, "w") as f:
        json.dump(area_boundry_serialized, f)

    return PATH_TO_VECTOR_DATA


def standarize_country_name(country: str) -> str:
    """Return the official country name using the input."""
    try:
        country_obj = (
            pycountry.countries.get(name=country)
            or pycountry.countries.get(alpha_2=country)
            or pycountry.countries.get(alpha_3=country)
        )
        if country_obj:
            return country_obj.name
        else:
            return country
    except KeyError:
        return country


def get_country_code(country: str) -> str:
    """Return the country code using the input."""
    try:
        country = standarize_country_name(country)
        country_obj = pycountry.countries.get(name=country)
        if country_obj:
            return country_obj.alpha_3
        else:
            return country
    except KeyError:
        return country
