# %%
import os

import ee
import geemap

ee.Initialize()
ROOT_DIR = "unicef-geospatial"
base_path = os.getcwd()
print(base_path)
idx = base_path.split("/").index(ROOT_DIR)

for _ in base_path.split("/")[idx + 1 :]:
    os.chdir("..")
os.chdir("unicef_geospatial")
print("Working on", os.getcwd())
from geospatial.droughts import get_drought_zones
from geospatial.geo_operations import (
    image_to_html,
    intersect_feature_collection,
    load_vector_data,
    save_vector_data,
)

# We'll try to answer the question:
# How many children are exposed to droughts in South Asia region?


sout_asian_countries = [
    "Afghanistan",
    "Bangladesh",
    "Bhutan",
    "India",
    "Maldives",
    "Nepal",
    "Pakistan",
    "Sri Lanka",
]


def getSouthAsiaRegion() -> ee.FeatureCollection:
    countries = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017").filter(
        ee.Filter.inList("country_na", sout_asian_countries)
    )
    return countries


# %%
south_asian_region = getSouthAsiaRegion()
south_asian_region.getInfo()
# %%
Map = geemap.Map()
Map.addLayer(south_asian_region, {"color": "red"}, "South Asian Region")
Map
# %%
all_south_asian = south_asian_region.union()
all_south_asian.getInfo()
Map = geemap.Map()
Map.addLayer(all_south_asian, {"color": "red"}, "South Asian Region")
Map
print(type(all_south_asian))
# %%
html = image_to_html(all_south_asian, "South Asian Region")
save_vector_data("data/south_asian_region.html", all_south_asian)
# %%
path_to_drought_zones = get_drought_zones(year=1990, month=1, day=1, spei_months=12)

# %%
intersection_path = intersect_feature_collection(
    ["data/south_asian_region.html", path_to_drought_zones]
)
# %%
print(intersection_path)
intersection = load_vector_data(intersection_path)
# %%
Map = geemap.Map()
Map.addLayer(intersection, {"color": "green"}, "Intersection")
Map.addLayer(all_south_asian, {"color": "red"}, "South Asian Region")
Map.addLayer(
    load_vector_data(path_to_drought_zones), {"color": "blue"}, "Drought Zones"
)
Map
# %%
