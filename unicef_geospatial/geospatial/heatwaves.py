import os
from pathlib import Path

import ee
from geospatial.geo_operations import save_ee_object
from langchain.tools import tool
from logging_config import get_logger
from utils.constants import HEATWAVE_DATASET, HEATWAVE_FILENAME
from utils.types import DECADES, METRICS

logger = get_logger(__name__)


@tool
def get_heatwave_image(
    metric: METRICS,
    decade: DECADES,
    temp_dir: str = "",
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

    Returns:
        The path to the saved heatwave image.
    """
    band = get_band_mapping(metric)

    logger.info(
        f"Getting heatwave image for decade {decade} and metric {metric} (band: {band})"
    )

    image = ee.Image(f"{HEATWAVE_DATASET}_{decade}")
    heatwave_tiff = image.select(band)

    try:
        save_ee_object(os.path.join(temp_dir, HEATWAVE_FILENAME), heatwave_tiff)
    except Exception as e:
        logger.error(f"Error saving heatwave image: {e}")
        pass

    logger.info("Returning image")
    return {
        "image_filename": HEATWAVE_FILENAME,
        "input_arguments": {"metric": metric, "decade": decade},
    }


def get_band_mapping(metric: str) -> str:
    """Get the band mapping for a heatwave metric."""
    return {
        "frequency": "b1",
        "duration": "b2",
        "severity": "b3",
        "extreme_high_temp": "b4",
    }[metric]
