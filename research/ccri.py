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
ee.Authenticate()
ee.Initialize(auth)

# %%
id = "projects/unicef-ccri/assets/coastal_flood_r100"  # 90m
threshold = 0

# %%
hazard_collection = ee.ImageCollection(id)
original_scale = hazard_collection.first().projection().nominalScale().getInfo()
original_crs = hazard_collection.first().projection().getInfo()
print(f"Original scale: {original_scale}")
print(f"Original CRS: {original_crs}")
hazard_layer = hazard_collection.mosaic()  # .reproject(
# crs="EPSG:4326", scale=original_scale
# )
new_scale = hazard_layer.projection().nominalScale().getInfo()
new_crs = hazard_layer.projection().getInfo()
print(f"New scale: {new_scale}")
print(f"New CRS: {new_crs}")
# scale = hazard_collection.first().projection().nominalScale()

scale = (
    ee.Image("projects/unicef-ccri/assets/heatwave_frequency_2014_2023_avg")
    .projection()
    .nominalScale()
    .getInfo()
)

# %%
hazard_collection.first().getInfo()
Map = geemap.Map()
Map.addLayer(hazard_collection.first(), {}, "Hazard layer")
Map.addLayer(hazard_layer, {}, "Hazard layer complete")
Map

# %%
start = time.time()
childpop = ee.ImageCollection(
    "projects/unicef-ccri/assets/childpop_constrained"
).mosaic()

# Filter the feature collection to only include Colombia (ISO3 code: COL)
aois = ee.FeatureCollection("projects/unicef-ccri/assets/" + "adm0" + "_simple")
aois = aois.filter(ee.Filter.eq("ISO3", "COL"))

exposed_population = childpop.updateMask(hazard_layer.gt(threshold))

print(
    f"exposed_population scale: {exposed_population.projection().nominalScale().getInfo()}"
)

populationByAOI = exposed_population.reduceRegions(
    collection=aois,
    reducer=ee.Reducer.sum(),
    scale=92.76624195666344,
    crs="EPSG:4326",
)

finalCollection = populationByAOI.map(
    lambda feature: feature.set("child_population_exposed", feature.get("sum"))
)

res = finalCollection.getInfo()
print(
    "child_population_exposed: ",
    res["features"][0]["properties"]["child_population_exposed"],
)
with open("finalCollection.json", "w") as f:
    f.write(str(res))
end = time.time()
print(f"Time taken: {end - start} seconds")
# %%
Map = geemap.Map()
Map.addLayer(finalCollection, {"min": 0, "max": 10000000}, "Population exposed")
Map.addLayer(exposed_population, {"color": "red"}, "Exposed population")
Map.addLayer(hazard_layer, {"color": "blue"}, "Hazard layer")
Map


# %%
