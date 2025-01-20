import ee
import geemap.foliumap as geemap
import pycountry
from utils.constants import ADMIN_LEVEL_1_BOUNDRIES_DATASET, COUNTRY_BOUNDRIES_DATASET
from utils.types import AREA_TYPES


def image_to_html(
    image: ee.Image,
    name: str = "",
    vis_params: dict = {},
    center: bool = False,
) -> str:
    """Converts an Earth Engine image to an HTML string."""
    demographic_map = geemap.Map()
    demographic_map.add_layer(image, vis_params, name)
    if center:
        demographic_map.center_object(image)
    html = demographic_map.to_html()
    if html is None:
        error_msg = "Failed to generate map"
        raise ValueError(error_msg)

    return html


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
        area_boundry = countries_boundries.filter(ee.Filter.eq("country_na", area_name))
    else:
        admin_level_1_boundries = ee.FeatureCollection(ADMIN_LEVEL_1_BOUNDRIES_DATASET)
        area_boundry = admin_level_1_boundries.filter(
            ee.Filter.eq("shapeName", area_name)
        )
    dataset_clipped = (
        dataset.setDefaultProjection(dataset.projection())
        .clip(area_boundry)
        .set("system:footprint", area_boundry.geometry())
    )
    return dataset_clipped
