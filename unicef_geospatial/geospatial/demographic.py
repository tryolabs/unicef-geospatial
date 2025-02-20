import json

import pycountry
from ee.featurecollection import FeatureCollection
from ee.filter import Filter
from ee.imagecollection import ImageCollection
from geospatial.geo_operations import (
    image_to_html,
    save_html,
    save_vector_data,
)
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
PATH_TO_DEMOGRAPHIC_IMAGE = "unicef_geospatial/data/demographic_image.json"


@tool
def get_population_image(
    age_group: AGE_GROUPS = "Total Population",
    sex: SEXES = "b",
) -> dict[str, str]:
    """Get population data image for a specific age group and sex.

    Retrieves demographic data from Earth Engine and saves it as a vector file.

    Args:
        age_group: Age group to analyze. Must be one of the valid AGE_GROUPS.
        sex: Sex to analyze. Must be one of the valid SEXES ('m', 'f', or 'b' for both).

    Returns:
        dict[str, str]: A dictionary containing:
            - path_to_image: Path to the saved demographic image file

    Raises:
        ValueError: If no demographic data is found for the given age group and sex.
    """
    logger = get_logger(__name__)

    demographic = ImageCollection(DEMOGRAPHIC_DATASET)
    demographic_image = (
        demographic.filter(Filter.eq("Age_Group", age_group))
        .filter(Filter.eq("Sex", sex))
        .first()
    )

    demographic_image = demographic_image.select(DEMOGRAPHIC_BAND)
    if demographic_image is None:
        logger.error("No demographic image found for the given age group and sex")
        raise ValueError("No demographic image found for the given age group and sex")

    save_vector_data(PATH_TO_DEMOGRAPHIC_IMAGE, demographic_image)

    return {"path_to_image": PATH_TO_DEMOGRAPHIC_IMAGE}


@tool
def get_zone_of_area(area_name: str, area_type: AREA_TYPES) -> dict[str, str]:
    """Get the zone boundary for a specified area and save it as a vector file.

    Retrieves the boundary geometry for either a country or admin level 1 area from
    Earth Engine and saves it as a GeoJSON file.

    Args:
        area_name: Name of the area to get boundary for. Must match names in the
            corresponding Earth Engine dataset.
        area_type: Type of area - either 'country' or 'admin1'. Determines which
            dataset to query.

    Returns:
        dict[str, str]: A dictionary containing:
            - value: Path to the saved GeoJSON vector file

    Example:
        To get boundary data for France:
        >>> zone_path = get_zone_of_area("France", "country")

        To get boundary data for California:
        >>> zone_path = get_zone_of_area("California", "admin1")
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

    return {"value": PATH_TO_VECTOR_DATA}


def standarize_country_name(country: str) -> str:
    """Standardize a country name to its official form.

    Uses pycountry to look up the official name of a country from various input formats.

    Args:
        country: Country name, 2-letter code, or 3-letter code to standardize.

    Returns:
        str: Official country name if found, otherwise returns the input unchanged.
    """
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
    """Get the 3-letter ISO country code for a country.

    Standardizes the country name first, then looks up its ISO 3166-1 alpha-3 code.

    Args:
        country: Country name, 2-letter code, or 3-letter code to look up.

    Returns:
        str: 3-letter ISO country code if found, otherwise returns the input unchanged.
    """
    try:
        country = standarize_country_name(country)
        country_obj = pycountry.countries.get(name=country)
        if country_obj:
            return country_obj.alpha_3
        else:
            return country
    except KeyError:
        return country
