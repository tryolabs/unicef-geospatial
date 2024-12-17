import ee
from utils.constants import COUNTRY_BOUNDRIES_DATASET


def filter_dataset_by_country(
    dataset: ee.Image, country: str
) -> tuple[ee.Image, ee.FeatureCollection]:
    countries_boundries = ee.FeatureCollection(COUNTRY_BOUNDRIES_DATASET)
    country_boundry = countries_boundries.filter(ee.Filter.eq("country_na", country))
    return dataset.clip(country_boundry), country_boundry
