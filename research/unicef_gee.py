# %%
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import ee

auth_path = Path("../ee_auth.json")
auth_file = auth_path.read_text()
auth_dict = json.loads(auth_file)
email = auth_dict["client_email"]

auth = ee.ServiceAccountCredentials(email=email, key_data=auth_file)

# %%
ee.Authenticate()
ee.Initialize(auth)
# %%
# list all assets
ee.data.listAssets({"parent": "projects/unicef-ccri/assets/"})
# %%
asset_id = "projects/unicef-ccri/assets/heatwave"
asset = ee.ImageCollection(asset_id)
asset.getInfo()

# %%
image_id = "projects/unicef-ccri/assets/heatwave/average_hwi_1960s"
image = ee.Image(image_id)
image.getInfo()
# %%
import geemap

band = image.select("b4")
Map = geemap.Map()
Map.addLayer(
    band,
    {"min": 0, "max": 30, "palette": ["blue", "green", "yellow", "red"]},
    "Heatwave",
)
Map
# %%
import ee
from langchain.tools import tool
from logging_config import get_logger
from utils.constants import PATH_TO_MAP
from utils.types import AREA_TYPES, DECADES, METRICS, REDUCERS

from unicef_geospatial.geospatial.demographic.utils import (
    filter_dataset_by_area,
    standarize_country_name,
)
from unicef_geospatial.geospatial.geo_operations import image_to_html

logger = get_logger(__name__)


def get_band_mapping(metric: str) -> dict:
    """Get the band mapping for a heatwave metric."""
    return {
        "frequency": "b1",
        "duration": "b2",
        "severity": "b3",
        "extreme_high_temp": "b4",
    }[metric]


@tool
def get_heatwave_metric_for_area(
    metric: METRICS,
    decade: DECADES,
    area_name: str,
    area_type: AREA_TYPES = "country",
    reducer: REDUCERS = "mean",
) -> dict:
    """Get the value of a heatwave metric for a specific area and decade.

    A heatwave is defined as 3+ consecutive days where max temp is in top 10%
    of local 15-day average (1960-1990 baseline).

    Args:
        metric: One of:
            - 'frequency': Number of heatwave events per year
            - 'duration': Average length of heatwave events in days
            - 'severity': Average degrees Celsius above heatwave threshold
            - 'extreme_high_temp': Average annual days exceeding 35°C
        decade: One of '1960s', '1970s', '1980s', '1990s', '2000s', '2010s', '2020s'
        area_name: Name of the area (country or admin level 1)
        area_type: Type of area - either 'country' or 'admin1'. Defaults to 'country'
        reducer: The reducer to use ('mean', 'max', 'min', etc). Defaults to 'mean'

    Returns:
        The value of the heatwave metric for the specified area and decade.
    """
    band = get_band_mapping(metric)
    image_collection = ee.ImageCollection(
        f"projects/unicef-ccri/assets/heatwave/average_hwi_{decade}"
    )
    heatwave_tiff = ee.Image(image_collection.select(band).first())

    logger.info(
        f"Heatwave image for decade {decade} and metric {metric} (band: {band})"
    )

    if area_type == "country":
        area_name = standarize_country_name(area_name)

    area_data = filter_dataset_by_area(heatwave_tiff, area_name, area_type)

    try:
        vis_params = {
            "min": 0,
            "max": 30,
            "palette": ["blue", "yellow", "red"],
        }
        logger.info("Going to generate HTML map")
        html = image_to_html(
            area_data, name=f"{area_name} Heatwaves", vis_params=vis_params, center=True
        )
        logger.info("Saving map to %s", PATH_TO_MAP)
        with open(PATH_TO_MAP, "w") as f:
            logger.info("Writing map to %s", PATH_TO_MAP)
            f.write(html)

    except Exception as e:
        logger.error(f"Error generating map: {e}")
        pass

    logger.info("Reducing region")
    stats = area_data.reduceRegion(
        reducer=getattr(ee.Reducer, reducer)(),
        geometry=area_data.get("system:footprint"),
        scale=1000,
        maxPixels=1e13,
    )

    logger.info("Returning stats")
    return {
        "value": round(stats.getInfo()["b1"], 3),
        "path_to_map": PATH_TO_MAP,
    }


# %%
