import ee
from geospatial.geo_operations import image_to_html, load_vector_data, save_html
from langchain.tools import tool
from logging_config import get_logger
from utils.constants import PATH_TO_MAP
from utils.types import DECADES, METRICS, REDUCERS

logger = get_logger(__name__)


@tool
def get_heatwave_metric_for_zone(
    metric: METRICS,
    decade: DECADES,
    path_to_vector_data: str,
    reducer: REDUCERS = "mean",
) -> dict:
    """Get the value of a heatwave metric for a specific zone and decade.

    A heatwave is defined as 3+ consecutive days where max temp is in top 10%
    of local 15-day average (1960-1990 baseline).

    Args:
        metric: One of:
            - 'frequency': Number of heatwave events per year
            - 'duration': Average length of heatwave events in days
            - 'severity': Average degrees Celsius above heatwave threshold
            - 'extreme_high_temp': Average annual days exceeding 35°C
        decade: One of '1960s', '1970s', '1980s', '1990s', '2000s', '2010s', '2020s'
        path_to_vector_data: Path to the geometry to clip the heatwave data
        reducer: The reducer to use ('mean', 'max', 'min', etc). Defaults to 'mean'

    Returns:
        The value of the heatwave metric for the specified zone and decade.
    """
    band = get_band_mapping(metric)
    image = ee.Image(f"projects/unicef-ccri/assets/heatwave/average_hwi_{decade}")
    zone_vector = load_vector_data(path_to_vector_data)
    image = image.clip(zone_vector).set("system:footprint", zone_vector.geometry())
    heatwave_tiff = image.select(band)

    logger.info(
        f"Heatwave image for decade {decade} and metric {metric} (band: {band})"
    )

    try:
        vis_params = {
            "min": 0,
            "max": 30,
            "palette": ["blue", "yellow", "red"],
        }
        logger.info("Going to generate HTML map")
        html = image_to_html(
            heatwave_tiff, name="Zone Heatwaves", vis_params=vis_params, center=True
        )
        save_html(PATH_TO_MAP, html)

    except Exception as e:
        logger.error(f"Error generating map: {e}")
        pass

    logger.info("Reducing region")

    stats = heatwave_tiff.reduceRegion(
        reducer=getattr(ee.Reducer, reducer)(),
        geometry=zone_vector,
        scale=1000,
        maxPixels=1e13,
    )
    logger.info("Returning stats")
    return {
        "value": round(stats.getInfo()[band], 3),
        "path_to_map": PATH_TO_MAP,
    }


def get_band_mapping(metric: str) -> str:
    """Get the band mapping for a heatwave metric."""
    return {
        "frequency": "b1",
        "duration": "b2",
        "severity": "b3",
        "extreme_high_temp": "b4",
    }[metric]
