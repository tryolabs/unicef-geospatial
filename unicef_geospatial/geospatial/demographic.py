import os

import ee
import pycountry
from ee.featurecollection import FeatureCollection
from ee.filter import Filter
from logging_config import get_logger
from utils.constants import (
    ADMIN_LEVEL_1_BOUNDRIES_DATASET,
    COUNTRY_BOUNDRIES_DATASET,
    FEATURE_COLLECTION_FILENAME,
)
from utils.io import save_ee_object
from utils.types import AREA_TYPES

logger = get_logger(__name__)

TH_SHAPE_AREA = 33


def get_zone_of_area(
    area_name: str, area_type: AREA_TYPES, temp_dir: str = ""
) -> dict[str, str]:
    """Get the zone boundary for a specified area and save it as a vector file.

    Retrieves the boundary geometry for either a country or admin level 1 area from
    Earth Engine and saves it as a GeoJSON file.

    Args:
        area_name: Name of the area to get boundary for.
                If it is a country, it should be the ISO 3166-1 alpha-3 code.
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
        area_name = get_country_code(area_name)
        countries_boundries = FeatureCollection(COUNTRY_BOUNDRIES_DATASET)

        area_boundry = countries_boundries.filter(Filter.eq("iso3", area_name))

        shape_area = area_boundry.first().getNumber("Shape_Area")

        simplification_tolerance = ee.Algorithms.If(
            shape_area.gt(ee.Number(TH_SHAPE_AREA)), 10000, 100
        )

        area_boundry = FeatureCollection(
            area_boundry.geometry().simplify(simplification_tolerance)
        )

    else:
        admin_level_1_boundries = FeatureCollection(ADMIN_LEVEL_1_BOUNDRIES_DATASET)
        area_boundry = admin_level_1_boundries.filter(Filter.eq("shapeName", area_name))

    filename = FEATURE_COLLECTION_FILENAME.replace(".json", f"_{area_name}.json")

    save_ee_object(os.path.join(temp_dir, filename), area_boundry)

    return {
        "value": filename,
        "input_arguments": {"area_name": area_name, "area_type": area_type},
    }


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
