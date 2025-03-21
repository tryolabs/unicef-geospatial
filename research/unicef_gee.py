# %%
import json
import os
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

sys.path.append(str(Path(__file__).parent.parent) + "/unicef_geospatial")
os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent) + "/unicef_geospatial"

import ee
import geemap

auth_path = Path("../ee_auth.json")
auth_file = auth_path.read_text()
auth_dict = json.loads(auth_file)
email = auth_dict["client_email"]

auth = ee.ServiceAccountCredentials(email=email, key_data=auth_file)

# %%
ee.Authenticate()
ee.Initialize(auth)
# %%
ee.data.listAssets({"parent": "projects/unicef-ccri/assets"})
# %%
# Reload the module to ensure we have the latest version
import importlib

if "geospatial.geo_operations" in sys.modules:
    importlib.reload(sys.modules["geospatial.geo_operations"])
from ee.reducer import Reducer
from geospatial.demographic import get_zone_of_area
from geospatial.geo_operations import (
    filter_image_by_threshold,
    get_dataset_image_and_metadata,
    load_vector_data,
    reduce_image,
    save_vector_data,
)
from utils.constants import EARTH_GEOMETRY_COORDS, EARTH_GEOMETRY_CRS

# %%
# esto de aca es coastal floods en Colombia (tendria que dar 22714)
country = "Colombia"
path_to_country = get_zone_of_area(country, "country")["value"]
coastal_flood_image_path = get_dataset_image_and_metadata("coastal_flood")[
    "path_to_image"
]
# filtered_coastal_flood_image_path = filter_image_by_threshold(
#     coastal_flood_image_path, 0
# )["path_to_image"]
demographic_image_path = get_dataset_image_and_metadata("children_population")[
    "path_to_image"
]
exposed_population = load_vector_data(demographic_image_path).updateMask(
    load_vector_data(coastal_flood_image_path).gt(0)
)
exposed_population_path = "exposed_population.json"
save_vector_data(exposed_population_path, exposed_population)
# intersection_path = intersect_feature_collection(
#     [path_to_country, filtered_coastal_flood_image_path]
# )["path_to_vector_data"]
reduce_image(exposed_population_path, path_to_country, "sum")
# %%
Map = geemap.Map()
Map.addLayer(load_vector_data(path_to_country), {}, "Country")
Map.addLayer(load_vector_data(demographic_image_path), {}, "Demographic")
# Map.addLayer(load_vector_data(intersection_path), {}, "Intersection")
Map.addLayer(load_vector_data(exposed_population_path), {}, "Exposed population")
Map
# %%

#

# %%
demographic_image_masked_path = (
    "../unicef_geospatial/data/demographic_image_masked.json"
)
map_zones_feature_collection_path = (
    "../unicef_geospatial/data/map_zones_feature_collection.json"
)
coastal_flood_image_path = "../unicef_geospatial/data/coastal_flood_image.json"
demographic_image_masked = load_vector_data(demographic_image_masked_path)
map_zones_feature_collection = load_vector_data(map_zones_feature_collection_path)
coastal_flood_image = load_vector_data(coastal_flood_image_path)
# %%
Map = geemap.Map()
Map.addLayer(demographic_image_masked, {}, "Demographic Masked")
Map.addLayer(map_zones_feature_collection, {}, "Map zones")
Map.addLayer(coastal_flood_image, {}, "Coastal flood")
Map
# %%
