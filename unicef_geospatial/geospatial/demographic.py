import json

import pycountry
from ee.featurecollection import FeatureCollection
from ee.filter import Filter
from langchain.tools import tool
from logging_config import get_logger
from utils.constants import (
    ADMIN_LEVEL_1_BOUNDRIES_DATASET,
    CHILDREN_DEMOGRAPHIC_DATASET,
    COUNTRY_BOUNDRIES_DATASET,
    PATH_TO_DEMOGRAPHIC_IMAGE,
    PATH_TO_VECTOR_DATA,
)
from utils.types import AREA_TYPES, DatasetMetadata

logger = get_logger(__name__)


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
    logger.info("Getting zone of area")
    if area_type == "country":
        countries_boundries = FeatureCollection(COUNTRY_BOUNDRIES_DATASET)
        area_boundry = countries_boundries.filter(Filter.eq("country_na", area_name))
    else:
        admin_level_1_boundries = FeatureCollection(ADMIN_LEVEL_1_BOUNDRIES_DATASET)
        area_boundry = admin_level_1_boundries.filter(Filter.eq("shapeName", area_name))

    area_boundry_serialized = area_boundry.serialize()

    with open(PATH_TO_VECTOR_DATA, "w") as f:
        json.dump(area_boundry_serialized, f)

    return {
        "value": PATH_TO_VECTOR_DATA,
        "input_arguments": {"area_name": area_name, "area_type": area_type},
    }


def get_children_population_metadata() -> DatasetMetadata:
    """Get children population metadata.

    Retrieves demographic data from Earth Engine and saves it as a vector file.

    Returns:
        DatasetMetadata: The children population metadata
    """
    logger.info("Getting children population information")
    metadata = DatasetMetadata(
        path_to_image=PATH_TO_DEMOGRAPHIC_IMAGE,
        asset_id=CHILDREN_DEMOGRAPHIC_DATASET,
        description="Population of children between 0-18 years old.",
    )

    return metadata


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
