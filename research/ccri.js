// Create a mosaic from the child population image collection.
// This combines multiple images into one continuous image.
var childpop = ee
  .ImageCollection("projects/unicef-ccri/assets/childpop_constrained")
  .mosaic();

// Define a list of hazard datasets. Each object contains:
// - id: the asset ID in Earth Engine
// - threshold: the threshold value to determine exposure (or 'Mean' for dynamic calculation)
// - name: a descriptive name for the hazard dataset
var hazards = [
  // {id: "projects/unicef-ccri/assets/river_flood_r100", threshold: 0.01, name: "river_flood_100yr_jrc_2024"},
  {
    id: "projects/unicef-ccri/assets/coastal_flood_r100",
    threshold: 0,
    name: "coastal_flood_100yr_jrc_2024",
  },
  // {id: "projects/unicef-ccri/assets/JBA_FLSW_resampled", threshold: 0, name: "pluvial_flood_100yr_jbl_2024"},
  // {id: "projects/unicef-ccri/assets/storm_giri_rp100", threshold: 17.5, name: "tropical_storm_100yr_giri_2024"},
  // {id: "projects/unicef-ccri/assets/ASI_cropland_avg_2014_2023", threshold: 50, name: "agricultural_drought_fao_1984-2023"},
  // {id: "projects/unicef-ccri/assets/sma_copernicus_avg_2015_2024", threshold: -1, name: "drought_sma_copernicus_1984-2023"},
  // {id: "projects/unicef-ccri/assets/spi_copernicus_avg_2015_2024", threshold: -1, name: "drought_spi_copernicus_1984-2023"},
  // {id: "projects/unicef-ccri/assets/heatwave_frequency_2014_2023_avg", threshold: 'Mean', name: "heatwave_frequency_ecmwf_2014-2024"}, // Example mean value: 6.03
  // {id: "projects/unicef-ccri/assets/heatwave_duration_2014_2023_avg", threshold: 'Mean', name: "heatwave_duration_ecmwf_2014-2024"}, // Example mean value: 35.99
  // {id: "projects/unicef-ccri/assets/heatwave_severity_2014_2023_avg", threshold: 'Mean', name: "heatwave_severity_ecmwf_2014-2024"}, // Example mean value: 21.19
  // {id: "projects/unicef-ccri/assets/extreme_heat_days_2014_2023_avg", threshold: 35, name: "extreme_heat_ecmwf_2014-2024"},
  // {id: "projects/unicef-ccri/assets/FIRMS_MODIS_Mean_Annual_FRP_2001_2023", threshold: 50, name: "fire_FRP_nasa_2001-2024"},
  // {id: "projects/unicef-ccri/assets/FIRMS_MODIS_Mean_Annual_Count_2001_2023", threshold: 10, name: "fire_frequency_nasa_2001-2023"},
  // {id: "projects/unicef-ccri/assets/sand_dust_storm_annual", threshold: 0, name: "sand_dust_storm_unccd_2024"},
  // {id: "projects/unicef-ccri/assets/pm25_2013_2022_avg", threshold: 5, name: "air_pollution_pm25_2012-2022"},
  // {id: "projects/unicef-ccri/assets/Pv_average_2013_2022", threshold: 0.001, name: "vectorborne_malariapv_2012-2022"},
  // {id: "projects/unicef-ccri/assets/Pf_average_2013_2022", threshold: 0.001, name: "vectorborne_malariapf_2012-2022"}
];

// Function to summarize population exposure for a given hazard and administrative level.
function summarizePopulation(hazard, adm_level) {
  var hazard_layer;

  // Determine how to load the hazard data based on its type.
  // For some hazards provided as an ImageCollection (e.g., river, coastal floods, tropical storms),
  // combine the images using .mosaic(). Otherwise, treat it as a single image.
  if (
    hazard.name === "river_flood_100yr_jrc_2024" ||
    hazard.name === "coastal_flood_100yr_jrc_2024" ||
    hazard.name === "tropical_storm_100yr_giri_2024"
  ) {
    hazard_layer = ee.ImageCollection(hazard.id).mosaic();
  } else {
    hazard_layer = ee.Image(hazard.id);
  }

  // Define a global geometry covering the entire Earth.
  var global_geometry = ee.Geometry.Polygon(
    [
      [
        [-180, 90],
        [-180, -90],
        [180, -90],
        [180, 90],
      ],
    ],
    null,
    false
  );

  // Use a reference image to obtain the target scale and projection.
  // This ensures that subsequent operations use a consistent spatial resolution.
  var referenceImage = ee.Image(
    "projects/unicef-ccri/assets/heatwave_frequency_2014_2023_avg"
  );
  var targetScale = referenceImage.projection().nominalScale();
  print("Target scale:", targetScale.getInfo());
  var targetCRS = referenceImage.projection();

  // Load global country boundaries.
  var countryBoundaries = ee.FeatureCollection(
    "projects/unicef-ccri/assets/admin0_wfp"
  );

  // Reproject the country boundaries to the target coordinate reference system.
  var countryBoundariesReprojected = countryBoundaries.map(function (feature) {
    return feature.transform(targetCRS);
  });

  // Determine the threshold (TH) to use for exposure.
  // If the threshold is set as 'Mean', calculate the mean hazard value over land.
  var TH = hazard.threshold;
  if (TH === "Mean") {
    // Create a land-sea mask by converting the reprojected country boundaries to a raster.
    // Land pixels will have a value of 1 and sea pixels will be 0.
    var landSeaMask = ee
      .Image(1)
      .clip(countryBoundariesReprojected) // Clip using the country boundaries
      .unmask(0) // Set pixels outside the boundaries (sea) to 0
      .reproject({
        crs: targetCRS,
        scale: targetScale,
      })
      .rename("landsea_mask");
    // Mask the hazard layer to include only land pixels using the landSeaMask.
    var hazard_layer_masked = hazard_layer.updateMask(landSeaMask);

    // Compute the mean hazard value over the global land area.
    TH = hazard_layer_masked
      .reduceRegion({
        reducer: ee.Reducer.mean(),
        geometry: global_geometry,
        scale: hazard_layer.projection().nominalScale(),
        bestEffort: true,
      })
      .values()
      .get(0);

    // Convert TH to an Earth Engine number.
    TH = ee.Number(TH);
    print("Mean TH on land:", TH);
  }

  var exposed_population;
  // Special handling for agricultural drought hazard.
  // For this hazard, apply a mask where the hazard value is less than or equal to 100,
  // then select the child population where the hazard value exceeds the threshold.
  if (hazard.name === "agricultural_drought_fao_1984-2023") {
    hazard_layer = hazard_layer.updateMask(hazard_layer.lte(100)); // Mask hazard values <= 100
    exposed_population = childpop.updateMask(hazard_layer.gt(TH)); // Mask child population where hazard > TH
  } else {
    // For other hazards, decide on the mask based on whether TH is negative or positive.
    if (TH < 0) {
      // For negative thresholds, mask where the hazard is less than TH.
      exposed_population = childpop.updateMask(hazard_layer.lt(TH));
    } else {
      // For positive thresholds, mask where the hazard is greater than TH.
      exposed_population = childpop.updateMask(hazard_layer.gt(TH));
    }
  }

  // Load administrative boundaries based on the provided admin level (e.g., 'adm0').
  var aois = ee.FeatureCollection(
    "projects/unicef-ccri/assets/" + adm_level + "_simple"
  );

  // Optionally, determine the scale dynamically from the hazard layer.
  var scale = hazard_layer.projection().nominalScale();

  // Aggregate the exposed population by each administrative unit.
  // The reduceRegions function sums the child population values within each AOI.
  var populationByAOI = exposed_population.reduceRegions({
    collection: aois,
    reducer: ee.Reducer.sum(),
    scale: 100, // Use a fixed scale (100 meters) for reduction
    crs: "EPSG:4326", // Export the results in WGS84 coordinate system
  });

  // Format the output by setting the 'child_population_exposed' property
  // to the computed sum for each administrative unit.
  var finalCollection = populationByAOI.map(function (feature) {
    return feature.set("child_population_exposed", feature.get("sum"));
  });

  // Export the final results as a CSV file to Google Drive.
  // Export.table.toDrive({
  //   collection: finalCollection,
  //   description: hazard.name + "_exposure_" + adm_level, // Description for the export task
  //   fileFormat: "CSV",
  //   selectors: ["ISO3", "child_population_exposed", "name"], // Columns to include in the CSV
  //   folder: "p1_exposure", // Google Drive folder to store the export
  // });
}

// Loop through each hazard in the hazards array and process them at the admin level 'adm0'.
hazards.forEach(function (hazard) {
  summarizePopulation(hazard, "adm0");
});
