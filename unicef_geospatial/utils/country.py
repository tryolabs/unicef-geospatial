import ee
import pycountry
from utils.constants import ADMIN_LEVEL_1_BOUNDRIES_DATASET, COUNTRY_BOUNDRIES_DATASET
from utils.types import AREA_TYPES


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


def filter_dataset_by_area(
    dataset: ee.Image, area_name: str, area_type: AREA_TYPES
) -> tuple[ee.Image, ee.FeatureCollection]:
    if area_type == "country":
        countries_boundries = ee.FeatureCollection(COUNTRY_BOUNDRIES_DATASET)
        country_boundry = countries_boundries.filter(
            ee.Filter.eq("country_na", area_name)
        )
    else:
        admin_level_1_boundries = ee.FeatureCollection(ADMIN_LEVEL_1_BOUNDRIES_DATASET)
        country_boundry = admin_level_1_boundries.filter(
            ee.Filter.eq("shapeName", area_name)
        )
    return dataset.clip(country_boundry), country_boundry
