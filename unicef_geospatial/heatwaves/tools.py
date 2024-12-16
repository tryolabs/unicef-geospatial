from typing import Literal

import ee
from langchain.tools import tool
from utils.country import standarize_country_name

METRICS = Literal["frequency", "duration", "severity", "extreme_high_temp"]
DECADES = Literal["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
COUNTRY_BOUNDRIES_DATASET = "USDOS/LSIB_SIMPLE/2017"
ADMIN_LEVEL_1_BOUNDRIES_DATASET = "WM/geoLab/geoBoundaries/600/ADM1"
REDUCERS = Literal["mean", "max", "min"]


@tool
def get_heatwave_metric_for_country(
    metric: METRICS, decade: DECADES, country: str, reducer: REDUCERS = "mean"
) -> dict:
    """Get the value of a heatwave metric for a specific country and decade.

    Args:
        metric: One of 'frequency', 'duration', 'severity', 'extreme_high_temp'
        decade: One of '1960s', '1970s', '1980s', '1990s', '2000s', '2010s', '2020s'
        country: Name of the country
        reducer: The reducer to use ('mean', 'max', 'min', etc). Defaults to 'mean'

    Returns:
        The value of the heatwave metric for the specified country and decade.
    """
    country = standarize_country_name(country)
    heatwave_tiff = ee.Image(
        f"projects/unicef-geospatial/assets/heatwaves/{metric}/average_heatwaves_{metric}_{decade}_proj_COG"
    )
    countries_boundries = ee.FeatureCollection(COUNTRY_BOUNDRIES_DATASET)

    country_boundries = countries_boundries.filter(ee.Filter.eq("country_na", country))
    country_heatwave = heatwave_tiff.clip(country_boundries)
    stats = country_heatwave.reduceRegion(
        reducer=getattr(ee.Reducer, reducer)(),
        geometry=country_boundries.geometry(),
        scale=1000,
        maxPixels=1e13,
    )
    return round(stats.getInfo()["b1"], 3)


@tool
def get_heatwave_metric_for_admin_level_1(
    metric: METRICS,
    decade: DECADES,
    admin_level_1_name: str,
    reducer: REDUCERS = "mean",
) -> dict:
    """Get the value of a heatwave metric for a specific city and decade.

    Args:
        metric: One of 'frequency', 'duration', 'severity', 'extreme_high_temp'
        decade: One of '1960s', '1970s', '1980s', '1990s', '2000s', '2010s', '2020s'
        admin_level_1_name: Name of the admin level 1, state, province, etc
        reducer: The reducer to use ('mean', 'max', 'min', etc). Defaults to 'mean'

    Returns:
        The value of the heatwave metric for the specified country and decade.
    """
    heatwave_tiff = ee.Image(
        f"projects/unicef-geospatial/assets/heatwaves/{metric}/average_heatwaves_{metric}_{decade}_proj_COG"
    )
    admin_level_1_boundries = ee.FeatureCollection(ADMIN_LEVEL_1_BOUNDRIES_DATASET)

    admin_level_1_boundries = admin_level_1_boundries.filter(
        ee.Filter.eq("shapeName", admin_level_1_name)
    )
    admin_level_1_heatwave = heatwave_tiff.clip(admin_level_1_boundries)
    stats = admin_level_1_heatwave.reduceRegion(
        reducer=getattr(ee.Reducer, reducer)(),
        geometry=admin_level_1_boundries.geometry(),
        scale=1000,
        maxPixels=1e13,
    )
    return round(stats.getInfo()["b1"], 3)
