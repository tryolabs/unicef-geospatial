from ee.filter import Filter
from ee.geometry import Geometry
from ee.imagecollection import ImageCollection
from geospatial.geo_operations import save_vector_data
from langchain.tools import tool
from logging_config import get_logger
from utils.constants import DROUGHT_DATASET, EARTH_GEOMETRY_COORDS, EARTH_GEOMETRY_CRS
from utils.types import DAYS, MONTHS

DROUGHT_THRESHOLD = -1.5
MAX_PIXELS = int(1e13)
MIN_AREA_KM2 = 100
AREA_SCALE = 1000
MAX_VERTICES = 1000

PATH_TO_VECTOR_DATA = "unicef_geospatial/data/drought_zones.json"


@tool
def get_drought_zones(
    year: int = 2000,
    month: MONTHS = 1,
    day: DAYS = 1,
    spei_months: int = 1,
) -> dict[str, str]:
    """Get drought zones and their vector representations for a given date.

    Identifies areas experiencing drought conditions based on the SPEI (Standardized
    Precipitation Evapotranspiration Index) dataset. Areas with SPEI values below
    DROUGHT_THRESHOLD are considered drought zones.

    Args:
        year (int): Year to analyze (e.g. 2000)
        month (MONTHS): Month to analyze (1-12)
        day (DAYS): Day to analyze (1-31)
        spei_months (int): Number of months over which SPEI was accumulated (1-48)
            - If 1, analyzes monthly drought conditions
            - If 12, analyzes yearly drought conditions

    Returns:
        dict[str, str]: Dictionary with the path to the serialized FeatureCollection of drought zones

    Example:
        To analyze yearly drought conditions globally in 2024:
        >>> zones = get_drought_zones(year=2024, month=1, day=1, spei_months=12)

    Notes:
        Only returns polygons larger than 100 km² to filter out noise.
    """
    logger = get_logger(__name__)
    spei_band = f"SPEI_{spei_months:02d}_month"
    drought_dataset = ImageCollection(DROUGHT_DATASET)
    drought_image = (
        drought_dataset.filter(
            Filter.eq("system:index", f"{year}_{month:02d}_{day:02d}")
        )
        .select(spei_band)
        .first()
    )
    scale = drought_image.select(spei_band).projection().nominalScale().getInfo()
    # Create mask where values are below threshold
    drought_mask = drought_image.unmask(-999).lt(DROUGHT_THRESHOLD)
    # Apply the mask to the original image
    masked_drought = drought_image.updateMask(drought_mask).toInt()
    try:
        earth_geometry = Geometry.Polygon(
            EARTH_GEOMETRY_COORDS,
            EARTH_GEOMETRY_CRS,
            False,
        )
        vectors = masked_drought.reduceToVectors(
            geometry=earth_geometry,
            scale=scale,
            geometryType="polygon",
            eightConnected=True,
            labelProperty="drought_value",
            maxPixels=1e9,
            crs=EARTH_GEOMETRY_CRS,
        )
        # Simplify geometries while preserving topology
        simplified_vectors = vectors.map(
            lambda f: f.simplify(MAX_VERTICES).set(
                {
                    "area_km2": f.geometry()
                    .area(AREA_SCALE)
                    .divide(AREA_SCALE),  # Add area in km² with error margin
                }
            )
        )
        # Filter out any invalid or tiny polygons
        final_vectors = simplified_vectors.filter(
            Filter.And(
                Filter.neq("drought_value", None),
                Filter.gt("area_km2", MIN_AREA_KM2),
            )
        )
        save_vector_data(PATH_TO_VECTOR_DATA, final_vectors)

    except Exception as e:
        logger.error(f"Error in vector conversion: {str(e)}")
        return ""

    return {"path_to_vector_data": PATH_TO_VECTOR_DATA}
