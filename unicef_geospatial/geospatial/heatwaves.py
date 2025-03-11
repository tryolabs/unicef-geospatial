# import ee
# from geospatial.geo_operations import save_vector_data
# from langchain.tools import tool
# from logging_config import get_logger
# from utils.types import DECADES, METRICS

# logger = get_logger(__name__)

# PATH_TO_HEATWAVE = "unicef_geospatial/data/heatwave_image.json"


# @tool
# def get_heatwave_image(
#     metric: METRICS,
#     decade: DECADES,
# ) -> dict:
#     """Get the value of a heatwave metric for a specific zone and decade.

#     A heatwave is defined as 3+ consecutive days where max temp is in top 10%
#     of local 15-day average (1960-1990 baseline).

#     Args:
#         metric: One of:
#             - 'frequency': Number of heatwave events per year
#             - 'duration': Average length of heatwave events in days
#             - 'severity': Average degrees Celsius above heatwave threshold
#             - 'extreme_high_temp': Average annual days exceeding 35°C
#         decade: One of '1960s', '1970s', '1980s', '1990s', '2000s', '2010s', '2020s'

#     Returns:
#         The value of the heatwave metric for the specified zone and decade.
#     """
#     band = get_band_mapping(metric)

#     logger.info(
#         f"Getting heatwave image for decade {decade} and metric {metric} (band: {band})"
#     )

#     image = ee.Image(f"projects/unicef-ccri/assets/heatwave/average_hwi_{decade}")
#     heatwave_tiff = image.select(band)

#     try:
#         save_vector_data(PATH_TO_HEATWAVE, heatwave_tiff)
#     except Exception as e:
#         logger.error(f"Error saving heatwave image: {e}")
#         pass

#     logger.info("Returning image")
#     return {
#         "path_to_image": PATH_TO_HEATWAVE,
#         "input_arguments": {"metric": metric, "decade": decade},
#     }


# def get_band_mapping(metric: str) -> str:
#     """Get the band mapping for a heatwave metric."""
#     return {
#         "frequency": "b1",
#         "duration": "b2",
#         "severity": "b3",
#         "extreme_high_temp": "b4",
#     }[metric]
