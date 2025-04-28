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
    {
        "id": "projects/unicef-ccri/assets/river_flood_r100",
        "threshold": 0.01,
        "name": "river_flood_100yr_jrc_2024",
    },
    {
        "id": "projects/unicef-ccri/assets/coastal_flood_r100",
        "threshold": 0,
        "name": "coastal_flood_100yr_jrc_2024",
    },
    {
        "id": "projects/unicef-ccri/assets/storm_giri_rp100",
        "threshold": 17.5,
        "name": "tropical_storm_100yr_giri_2024",
    },
    {
        "id": "projects/unicef-ccri/assets/ASI_return_level_100yr",
        "threshold": 30,
        "name": "agricultural_drought_fao_1984-2023",
    },
    {
        "id": "projects/unicef-ccri/assets/spei12_period_mean_2014_2024",
        "threshold": -1,
        "name": "drought_spei_copernicus_2014-2024",
    },
    {
        "id": "projects/unicef-ccri/assets/spi12_period_mean_2014_2024",
        "threshold": -1,
        "name": "drought_spi_copernicus_2014-2024",
    },
    {
        "id": "projects/unicef-ccri/assets/heatwave_frequency_return_level_100yr",
        "threshold": "Mean",  # 16.8
        "name": "heatwave_frequency_ecmwf_2014-2024",
    },
    {
        "id": "projects/unicef-ccri/assets/heatwave_duration_return_level_100yr",
        "threshold": "Mean",  # 89.8
        "name": "heatwave_duration_ecmwf_2014-2024",
    },
    {
        "id": "projects/unicef-ccri/assets/heatwave_severity_return_level_100yr",
        "threshold": "Mean",  # 3.8
        "name": "heatwave_severity_ecmwf_2014-2024",
    },
    {
        "id": "projects/unicef-ccri/assets/high_temp_degree_days_return_level_100yr",
        "threshold": 35,
        "name": "extreme_heat_ecmwf_2014-2024",
    },
    {
        "id": "projects/unicef-ccri/assets/FIRMS_FRP_90th_percentile",
        "threshold": "Mean",
        "name": "fire_FRP_nasa_2001-2024",
    },
    {
        "id": "projects/unicef-ccri/assets/FIRMS_count_90th_percentile",
        "threshold": "Mean",
        "name": "fire_frequency_nasa_2001-2023",
    },
    {
        "id": "projects/unicef-ccri/assets/sand_dust_storm_annual",
        "threshold": 0,
        "name": "sand_dust_storm_unccd_2024",
    },
    {
        "id": "projects/unicef-ccri/assets/pm25_p90_1998_2023",
        "threshold": 5,
        "name": "air_pollution_pm25_1998-2023",
    },
    {
        "id": "projects/unicef-ccri/assets/Pv_average_2013_2022",
        "threshold": 0.001,
        "name": "vectorborne_malariapv_2012-2022",
    },
    {
        "id": "projects/unicef-ccri/assets/Pf_average_2013_2022",
        "threshold": 0.001,
        "name": "vectorborne_malariapf_2012-2022",
    },
]


def get_threshold(hazard_layer: ee.Image):
    print("Calculating mean threshold")
    # Create a land-sea mask by converting the reprojected country boundaries to a raster.
    # Land pixels will have a value of 1 and sea pixels will be 0.
    aois = ee.FeatureCollection("projects/unicef-ccri/assets/" + "adm0" + "_simple")

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
        .reproject(crs=targetCRS, scale=targetScale)
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
            reducer=ee.Reducer.mean(),
            geometry=global_geometry,
            scale=hazard_layer.projection().nominalScale(),
            bestEffort=True,
        )
        .values()
        .get(0)
    )
    return ee.Number(threshold)


# %%
countries = ["AGO", "NIC", "URY", "COL"]
full_df = pd.DataFrame(columns=["country", "id", "value"])
for hazard in all_hazards:
    df_hazard = pd.DataFrame(columns=["country", "id", "value"])
    for country in countries:
        id = hazard["id"]
        threshold = hazard["threshold"]
        print(f"Processing {id} with threshold {threshold} for {country}")
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
            threshold = get_threshold(hazard_layer)
        else:
            threshold = ee.Number(threshold)
        threshold_value = threshold.getInfo()
        print(f"Threshold: {threshold_value}")
        if id == "projects/unicef-ccri/assets/ASI_cropland_avg_2014_2023":
            print("Updating mask for agricultural drought")
            hazard_layer = hazard_layer.updateMask(hazard_layer.lte(100))
            exposed_population = childpop.updateMask(hazard_layer.gt(threshold))
        else:
            # For other hazards, decide on the mask based on whether TH is negative or positive.
            if threshold_value < 0:
                print("Updating mask for negative threshold")
                # For negative thresholds, mask where the hazard is less than TH.
                exposed_population = childpop.updateMask(hazard_layer.lt(threshold))
            else:
                print("Updating mask for positive threshold")
                # For positive thresholds, mask where the hazard is greater than TH.
                exposed_population = childpop.updateMask(hazard_layer.gt(threshold))

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
        print(
            f"Finish processing, {id} with threshold {threshold_value} for {country}",
            flush=True,
        )

        # Convert results to DataFrame
        features = res["features"]
        data = []
        for feature in features:
            properties = feature["properties"]
            data.append(properties)

        df = pd.DataFrame(data)
        df_hazard.loc[len(df_hazard)] = [country, id, df["child_population_exposed"]]
        full_df.loc[len(full_df)] = [country, id, df["child_population_exposed"]]

    # Export to CSV
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{hazard['name']}_exposure_adm0.csv"
    df_hazard.to_csv(output_file, index=False)
    print(f"Results exported to {output_file}")

# output_file = Path("./output/all_hazards_exposure_adm0.csv")
# full_df.to_csv(output_file, index=False)

# # %%
# Map = geemap.Map()
# Map.addLayer(hazard_layer, {}, "Hazard")
# Map.addLayer(exposed_population, {}, "Exposed Population")
# Map.addLayer(childpop, {}, "Child Population")
# Map.addLayer(aois, {}, "AOIs")
# Map
# %%
# # %%
