import json

import geemap.foliumap as geemap
from ee.deserializer import fromJSON
from ee.errormargin import ErrorMargin
from ee.feature import Feature
from ee.featurecollection import FeatureCollection
from ee.image import Image
from ee.reducer import Reducer
from langchain.tools import tool
from logging_config import get_logger
from utils.constants import PATH_TO_MAP
from utils.types import REDUCERS

INTERSECTION_PATH = "unicef_geospatial/data/intersection.json"


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
    logger = get_logger(__name__)
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
    return {"path_to_vector_data": INTERSECTION_PATH}


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
    return stats


@tool
def build_map(
    path_to_image: str,
    path_to_vector_data: str,
    name: str = "",
    center: bool = True,
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
    vector_data = load_vector_data(path_to_vector_data)
    image = load_vector_data(path_to_image)
    return image_to_html(image=image, vector_data=vector_data, name=name, center=center)


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
    demographic_map = geemap.Map()
    clipped_image = image.clip(vector_data)
    demographic_map.add_layer(clipped_image, vis_params, name)
    if center:
        demographic_map.center_object(vector_data, max_error=0.1)
    demographic_map.to_html(PATH_TO_MAP)
    return {"path_to_map": PATH_TO_MAP}


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
        logger = get_logger(__name__)
        with open(path_to_vector_data, "r") as f:
            logger.info(f"Going to load vector data from {path_to_vector_data}")
            json_value = eval(f.read())
            vector_data = fromJSON(json_value)

        # Get the info without converting to Python dict
        if isinstance(vector_data, Image):
            return vector_data
        elif isinstance(vector_data, FeatureCollection):
            return vector_data
        else:
            raise ValueError(f"Unknown vector data type: {type(vector_data)}")

    except Exception as e:
        logger.error(f"Error in vector conversion: {str(e)}")
        raise e
