# %%
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd

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
all_hazards = [
    # {
    #     "id": "projects/unicef-ccri/assets/river_flood_r100",
    #     "threshold": 0.01,
    # },
    # {
    #     "id": "projects/unicef-ccri/assets/coastal_flood_r100",
    #     "threshold": 0,
    # },
    # {
    #     "id": "projects/unicef-ccri/assets/JBA_FLSW_resampled",
    #     "threshold": 0,
    # },
    # {
    #     "id": "projects/unicef-ccri/assets/storm_giri_rp100",
    #     "threshold": 17.5,
    # },
    # {
    #     "id": "projects/unicef-ccri/assets/ASI_cropland_avg_2014_2023",
    #     "threshold": 50,
    # },
    # {
    #     "id": "projects/unicef-ccri/assets/sma_copernicus_avg_2015_2024",
    #     "threshold": -1,
    # },
    # {
    #     "id": "projects/unicef-ccri/assets/spi_copernicus_avg_2015_2024",
    #     "threshold": -1,
    # },
    # {
    #     "id": "projects/unicef-ccri/assets/heatwave_frequency_2014_2023_avg",
    #     "threshold": "Mean",
    # },
    # {
    #     "id": "projects/unicef-ccri/assets/heatwave_duration_2014_2023_avg",
    #     "threshold": "Mean",
    # },
    # {
    #     "id": "projects/unicef-ccri/assets/heatwave_severity_2014_2023_avg",
    #     "threshold": "Mean",
    # },
    # {
    #     "id": "projects/unicef-ccri/assets/extreme_heat_days_2014_2023_avg",
    #     "threshold": 35,
    # },
    # {
    #     "id": "projects/unicef-ccri/assets/FIRMS_MODIS_Mean_Annual_FRP_2001_2023",
    #     "threshold": 50,
    # },
    {
        "id": "projects/unicef-ccri/assets/FIRMS_MODIS_Mean_Annual_Count_2001_2023",
        "threshold": 10,
    },
    # {
    #     "id": "projects/unicef-ccri/assets/sand_dust_storm_annual",
    #     "threshold": 0,
    # },
    # {
    #     "id": "projects/unicef-ccri/assets/pm25_2013_2022_avg",
    #     "threshold": 5,
    # },
    # {
    #     "id": "projects/unicef-ccri/assets/Pv_average_2013_2022",
    #     "threshold": 0.001,
    # },
    # {
    #     "id": "projects/unicef-ccri/assets/Pf_average_2013_2022",
    #     "threshold": 0.001,
    # },
]


def get_threshold(aois: ee.FeatureCollection, hazard_layer: ee.Image):
    print("Calculating mean threshold")
    # Create a land-sea mask by converting the reprojected country boundaries to a raster.
    # Land pixels will have a value of 1 and sea pixels will be 0.
    referenceImage = ee.Image(
        "projects/unicef-ccri/assets/heatwave_frequency_2014_2023_avg"
    )
    targetScale = referenceImage.projection().nominalScale()
    targetCRS = referenceImage.projection()

    countryBoundariesReprojected = aois.map(
        lambda feature: feature.transform(targetCRS)
    )

    landSeaMask = (
        ee.Image(1)
        .clip(countryBoundariesReprojected)
        .unmask(0)
        .reproject(
            {
                "crs": targetCRS,
                "scale": targetScale,
            }
        )
        .rename("landsea_mask")
    )

    # Mask the hazard layer to include only land pixels using the landSeaMask.
    hazard_layer_masked = hazard_layer.updateMask(landSeaMask)

    global_geometry = ee.Geometry.Polygon(
        [
            [
                [-180, 90],
                [-180, -90],
                [180, -90],
                [180, 90],
            ],
        ],
        None,
        False,
    )

    # Compute the mean hazard value over the global land area.
    threshold = (
        hazard_layer_masked.reduceRegion(
            {
                "reducer": ee.Reducer.mean(),
                "geometry": global_geometry,
                "scale": hazard_layer.projection().nominalScale(),
                "bestEffort": True,
            }
        )
        .values()
        .get(0)
    )
    print("Mean threshold on land:", threshold)


# %%
country = "COL"
for hazard in all_hazards:
    id = hazard["id"]
    threshold = hazard["threshold"]
    print(f"Processing {id} with threshold {threshold}")
    if (
        id == "projects/unicef-ccri/assets/river_flood_r100"
        or id == "projects/unicef-ccri/assets/coastal_flood_r100"
        or id == "projects/unicef-ccri/assets/storm_giri_rp100"
    ):
        hazard_layer = ee.ImageCollection(id).mosaic()
    else:
        hazard_layer = ee.Image(id)

    childpop = ee.ImageCollection(
        "projects/unicef-ccri/assets/childpop_constrained"
    ).mosaic()

    aois = ee.FeatureCollection("projects/unicef-ccri/assets/" + "adm0" + "_simple")
    if country:
        print("Filtering by country")
        aois = aois.filter(ee.Filter.eq("ISO3", country))

    if threshold == "Mean":
        threshold = get_threshold(aois, hazard_layer)

    if id == "projects/unicef-ccri/assets/ASI_cropland_avg_2014_2023":
        print("Updating mask for agricultural drought")
        hazard_layer = hazard_layer.updateMask(hazard_layer.lte(100))
        exposed_population = childpop.updateMask(hazard_layer.gt(ee.Number(threshold)))
    else:
        # For other hazards, decide on the mask based on whether TH is negative or positive.
        if threshold < 0:
            print("Updating mask for negative threshold")
            # For negative thresholds, mask where the hazard is less than TH.
            exposed_population = childpop.updateMask(
                hazard_layer.lt(ee.Number(threshold))
            )
        else:
            print("Updating mask for positive threshold")
            # For positive thresholds, mask where the hazard is greater than TH.
            exposed_population = childpop.updateMask(
                hazard_layer.gt(ee.Number(threshold))
            )

    populationByAOI = exposed_population.reduceRegions(
        collection=aois,
        reducer=ee.Reducer.sum(),
        scale=100,
        crs="EPSG:4326",
    )

    finalCollection = populationByAOI.map(
        lambda feature: feature.set("child_population_exposed", feature.get("sum"))
    )

    res = finalCollection.getInfo()

    print(f"Finish processing, {id} with threshold {threshold}", flush=True)
    print("Saving results to csv", flush=True)

    # Convert results to DataFrame
    features = res["features"]
    data = []
    for feature in features:
        properties = feature["properties"]
        data.append(properties)

    df = pd.DataFrame(data)
    # Export to CSV
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{id.split('/')[-1]}_exposure_adm0.csv"
    df.to_csv(output_file, index=False)
    print(f"Results exported to {output_file}")
# %%
df.head()
# %%
Map = geemap.Map()
Map.addLayer(hazard_layer, {}, "Hazard")
Map.addLayer(exposed_population, {}, "Exposed Population")
Map.addLayer(childpop, {}, "Child Population")
Map.addLayer(aois, {}, "AOIs")
Map
# %%
Map.to_html()
# %%
