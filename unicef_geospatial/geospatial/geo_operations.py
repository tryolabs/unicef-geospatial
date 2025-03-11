import json

import geemap.foliumap as geemap
from ee.deserializer import fromJSON
from ee.errormargin import ErrorMargin
from ee.feature import Feature
from ee.featurecollection import FeatureCollection
from ee.filter import Filter
from ee.geometry import Geometry
from ee.image import Image
from ee.imagecollection import ImageCollection
from ee.reducer import Reducer
from geospatial.earth_engine import get_dataset_metadata
from langchain.tools import tool
from logging_config import get_logger
from utils.constants import EARTH_GEOMETRY_COORDS, EARTH_GEOMETRY_CRS, PATH_TO_MAP
from utils.types import ALL_DATASETS, REDUCERS

INTERSECTION_PATH = "unicef_geospatial/data/intersection.json"
logger = get_logger(__name__)

MAX_PIXELS = int(1e13)
MIN_AREA_KM2 = 100
MAX_VERTICES = 10


@tool
def get_dataset_image_and_metadata(
    dataset: ALL_DATASETS,
) -> dict[str, str]:
    """Get an image from Earth Engine and save it as a vector data.

    Args:
        dataset: The dataset to get the image and metadata for

    Returns:
        # The path to the saved vector data
    """
    metadata = get_dataset_metadata(dataset)
    logger.info(f"Getting image from {metadata.asset_id}")
    if metadata.mosaic:
        image = ImageCollection(metadata.asset_id).mosaic()
    else:
        image = Image(metadata.asset_id)
    save_vector_data(metadata.path_to_image, image)
    return {
        "path_to_image": metadata.path_to_image,
        "asset_id": metadata.asset_id,
        "mosaic": metadata.mosaic,
        "threshold": metadata.threshold,
        "greater_than": metadata.greater_than,
        "input_arguments": {
            "dataset": dataset,
        },
    }


@tool
def filter_image_by_threshold(
    path_to_image: str, threshold: float, greater_than: bool = True
) -> str:
    """Filter an image by a threshold.

    This function is useful for extracting specific zones from continuous data based on a threshold value.
    For example, when analyzing how many children are affected by droughts, you would need to define
    what constitutes a drought zone.

    The threshold is the value below which the data is considered to be in the drought zone.
    For example, for drought analysis, a threshold of -1.5 is used to identify drought zones.

    Args:
        path_to_image: The path to the image to filter
        threshold: The threshold to filter the image by. Values below this threshold will be kept
                  (for drought analysis, use -1.5 to identify drought zones)
        greater_than: Whether to keep values greater than the threshold

    Returns:
        The path to the filtered image
    """
    logger.info(f"Filtering image {path_to_image} by threshold: {threshold}")
    image = load_vector_data(path_to_image)
    if not isinstance(image, Image):
        raise TypeError(
            f"Expected an Earth Engine Image object, but got {type(image).__name__}. "
            f"Please provide a valid image path."
        )
    # Create a mask where values are less than threshold
    filtered_mask = image.gt(threshold) if greater_than else image.lt(threshold)
    # Apply the mask to the original image
    filtered = image.updateMask(filtered_mask).toInt()
    geometry = Geometry.Polygon(
        EARTH_GEOMETRY_COORDS,
        EARTH_GEOMETRY_CRS,
        False,
    )
    scale = filtered.projection().nominalScale().getInfo()
    logger.info(f"Scale: {scale}")
    # Convert to vectors with explicit geometry to avoid EEException
    vectors = filtered.reduceToVectors(
        scale=scale,
        geometry=geometry,
        geometryType="polygon",
        eightConnected=True,
        labelProperty="value",
        maxPixels=1e13,
    )

    simplified_vectors = vectors.map(
        lambda f: f.simplify(MAX_VERTICES).set(
            {
                "area_km2": f.geometry()
                .area(scale)
                .divide(scale),  # Add area in km² with error margin
            }
        )
    )
    # Filter out any invalid or tiny polygons
    final_vectors = simplified_vectors.filter(
        Filter.And(
            Filter.neq("value", None),
            Filter.gt("area_km2", MIN_AREA_KM2),
        )
    )
    path_to_filtered_image = path_to_image.replace(".json", "_filtered.json")
    save_vector_data(path_to_filtered_image, final_vectors)
    return {
        "path_to_image": path_to_filtered_image,
    }


@tool
def intersect_feature_collection(
    paths_to_feature_collections: list[str],
) -> str:
    """Intersect a list of feature collections and return the resulting data.

    It is not possible to intersect images, just vector data.

    Args:
        paths_to_feature_collections: List of paths to the feature collections/images to intersect

    Returns:
        dict: Dictionary containing paths to the intersection result and HTML visualization
    """
    logger.info("Intersecting data: %s", paths_to_feature_collections)

    if len(paths_to_feature_collections) == 0:
        raise ValueError("No feature collections provided")

    intersection = load_vector_data(paths_to_feature_collections[0])
    if isinstance(intersection, Image):
        # if images are intersected, the values of each are changed
        # only feature collections can be intersected
        raise ValueError("Image cannot be intersected")

    for path in paths_to_feature_collections[1:]:
        new_data = load_vector_data(path)
        if isinstance(new_data, Image):
            raise ValueError("Image cannot be intersected")
        intersection = intersection.map(lambda f: intersect_feature(f, new_data))

    save_vector_data(INTERSECTION_PATH, intersection)
    return {
        "path_to_vector_data": INTERSECTION_PATH,
        "input_arguments": {
            "paths_to_feature_collections": paths_to_feature_collections
        },
    }


@tool
def reduce_image(
    path_to_image: str,
    path_to_geometry: str,
    reducer: REDUCERS,
) -> dict:
    """Reduce an image by applying a reducer to its pixels.

    Args:
        path_to_image: The path to the image to reduce
        path_to_geometry: The path to the geometry to reduce the image to
        reducer: The reducer to apply

    Returns:
        dict: A dictionary containing the reduced value
    """
    logger.info(f"Reducing image with {reducer}")
    image = load_vector_data(path_to_image)
    scale = image.projection().nominalScale().getInfo()
    geometry = load_vector_data(path_to_geometry)
    reduced = image.reduceRegion(
        reducer=getattr(Reducer, reducer)(),
        geometry=geometry,
        scale=scale,
        maxPixels=1e13,
    )
    stats = reduced.getInfo()
    return {
        "stats": stats,
        "input_arguments": {
            "path_to_image": path_to_image,
            "path_to_geometry": path_to_geometry,
            "reducer": reducer,
        },
    }


@tool
def build_map(
    path_to_image: str,
    path_to_vector_data: str,
    name: str = "",
) -> dict:
    """Build a map from an image and vector data and save it to an HTML file.

    Creates an interactive map by overlaying an Earth Engine image on top of vector data
    (e.g. administrative boundaries). The map is saved as an HTML file that can be viewed
    in a web browser.

    Args:
        path_to_image: Path to the Earth Engine image file to display on the map
        path_to_vector_data: Path to the vector data file (e.g. GeoJSON) defining the
            boundaries to overlay the image on
        name: The name of the map
        center: Whether to center the map on the vector data

    Returns:
        dict: A dictionary containing the path to the saved HTML map file under the key
            'path_to_map'
    """
    logger.info(f"Building map with {path_to_image} and {path_to_vector_data}")
    vector_data = load_vector_data(path_to_vector_data)
    image = load_vector_data(path_to_image)
    return {
        "path_to_map": image_to_html(
            image=image, vector_data=vector_data, name=name, center=True
        ),
        "input_arguments": {
            "path_to_image": path_to_image,
            "path_to_vector_data": path_to_vector_data,
            "name": name,
        },
    }


def intersect_feature(feature_1: Feature, feature_2: Feature) -> Feature:
    """Intersect a feature with a feature collection.

    Computes the geometric intersection between a feature and a feature collection,
    preserving the properties of the input feature.

    Args:
        feature: The feature to intersect
        feature_collection: The feature collection to intersect with

    Returns:
        Feature: A new feature representing the intersection, with properties copied from
                the input feature
    """
    intersected = feature_1.geometry().intersection(
        feature_2.geometry(), ErrorMargin(100)
    )
    return Feature(intersected).copyProperties(feature_1)


def image_to_html(
    image: Image,
    vector_data: FeatureCollection,
    name: str = "",
    vis_params: dict = {},
    center: bool = True,
) -> str:
    """Converts an Earth Engine image to an HTML string."""
    logger.info("Converting image to HTML")
    demographic_map = geemap.Map()
    clipped_image = image.clip(vector_data)
    demographic_map.add_layer(clipped_image, vis_params, name)
    if center:
        demographic_map.center_object(vector_data, max_error=0.1)
    demographic_map.to_html(PATH_TO_MAP)
    return PATH_TO_MAP


def save_vector_data(path: str, vector_data: FeatureCollection | Image) -> None:
    """Save a vector data to a file."""
    logger = get_logger(__name__)
    logger.info("Saving vector data to %s", path)
    serialized_vector_data = vector_data.serialize()
    with open(path, "w") as f:
        logger.info("Writing vector data to %s", path)
        json.dump(serialized_vector_data, f)


def load_vector_data(path_to_vector_data: str) -> FeatureCollection | Image:
    """Load vector data from a JSON file and convert to Earth Engine FeatureCollection or Image.

    Args:
        path_to_vector_data: Path to the JSON file containing the vector data

    Returns:
        Either an Earth Engine FeatureCollection or Image object
    """
    try:
        with open(path_to_vector_data, "r") as f:
            logger.info(f"Going to load vector data from {path_to_vector_data}")
            vector_data = eval(f.read())
            vector_data = fromJSON(vector_data)
        # Get the info without converting to Python dict
        if isinstance(vector_data, Image):
            logger.info("Vector data is an image")
            return vector_data
        elif isinstance(vector_data, FeatureCollection):
            logger.info("Vector data is a feature collection")
            return vector_data
        else:
            if vector_data.getInfo().get("type") == "Image":
                logger.info("Vector data is an image")
                return Image(vector_data)
            elif vector_data.getInfo().get("type") == "FeatureCollection":
                logger.info("Vector data is a feature collection")
                return FeatureCollection(vector_data)
            raise ValueError(f"Unknown vector data type: {type(vector_data)}")

    except Exception as e:
        logger.error(f"Error in vector conversion: {str(e)}")
        raise e
