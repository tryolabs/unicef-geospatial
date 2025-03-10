# %%
import json
import os
import sys
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
# list all assets
# ee.data.listAssets({"parent": "projects/unicef-ccri/assets/"})
# %%
# change python path to inside the unicef_geospatial folder
import os

from geospatial.floods import PATH_TO_RIVER_FLOOD, get_river_flood_image
from geospatial.geo_operations import load_vector_data

# path_to_river_flood = get_river_flood_image()
river_flood = load_vector_data(PATH_TO_RIVER_FLOOD)
# river_flood.getInfo()
# %%
from geospatial.geo_operations import (
    filter_image_by_threshold,
    save_vector_data,
)

path_to_filtered = filter_image_by_threshold(PATH_TO_RIVER_FLOOD, 3)
filtered = load_vector_data(path_to_filtered)

# %%
import geemap

Map = geemap.Map()
Map.addLayer(filtered, {"min": 0, "max": 1}, "River Flood Filtered")
Map.addLayer(river_flood, {"min": 0, "max": 1}, "River Flood")
Map
# %%
from geospatial.droughts import get_drought_zones

drought_zones = get_drought_zones()
drought_zones = load_vector_data(drought_zones["path_to_vector_data"])
# %%
Map = geemap.Map()
Map.addLayer(drought_zones, {"min": 0, "max": 1}, "Drought Zones")
Map
# %%
