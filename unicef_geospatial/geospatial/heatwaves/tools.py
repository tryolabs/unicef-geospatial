import ee
from geospatial.demographic.utils import (
    filter_dataset_by_area,
    image_to_html,
    standarize_country_name,
)
from langchain.tools import tool
from logging_config import get_logger
from utils.constants import PATH_TO_MAP
from utils.types import AREA_TYPES, DECADES, METRICS, REDUCERS

logger = get_logger(__name__)


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
    heatwave_tiff = ee.Image(
        f"projects/unicef-geospatial/assets/heatwaves/{metric}/average_heatwaves_{metric}_{decade}_proj_COG"
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

        html = image_to_html(
            area_data, name=f"{area_name} Heatwaves", vis_params=vis_params, center=True
        )
        with open(PATH_TO_MAP, "w") as f:
            logger.info(f"Writing map to {PATH_TO_MAP}")
            f.write(html)

    except Exception as e:
        logger.error(f"Error generating map: {e}")
        pass

    stats = area_data.reduceRegion(
        reducer=getattr(ee.Reducer, reducer)(),
        geometry=area_data.get("system:footprint"),
        scale=1000,
        maxPixels=1e13,
    )

    return {
        "value": round(stats.getInfo()["b1"], 3),
        "path_to_map": PATH_TO_MAP,
    }
