# %%
import ee
import geemap.core as geemap
import ipywidgets as widgets
from IPython.display import display

ee.Authenticate()
ee.Initialize(project="unicef-geospatial")
# %%
metrics = ["duration", "extreme_high_temp", "frequency", "severity"]
decades = ["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]

asset_collections = []
for metric in metrics:
    asset_path = f"projects/unicef-geospatial/assets/heatwaves/{metric}"
    assets = ee.data.listAssets({"parent": asset_path})
    if "assets" in assets:
        asset_collections.extend(assets["assets"])

# Create dropdown widgets
metric_dropdown = widgets.Dropdown(
    options=metrics, description="Metric:", style={"description_width": "initial"}
)

decade_dropdown = widgets.Dropdown(
    options=decades, description="Decade:", style={"description_width": "initial"}
)

map = geemap.Map(center=[30, 0], zoom=2)


def update_map(metric, decade):
    map.clear_layers()
    asset_id = f"projects/unicef-geospatial/assets/heatwaves/{metric}/average_heatwaves_{metric}_{decade}_proj_COG"
    try:
        image = ee.Image(asset_id)
        vis_params = {
            "min": 0,
            "max": 100,
            "palette": "inferno",
        }
        map.add_layer(image, vis_params, f"Heatwave {metric} - {decade}")
    except:
        print(f"No data available for {metric} in {decade}")


# Create interactive controls
def on_change(change):
    if change["type"] == "change" and change["name"] == "value":
        update_map(metric_dropdown.value, decade_dropdown.value)


metric_dropdown.observe(on_change)
decade_dropdown.observe(on_change)

# Display widgets and map
# %%
display(widgets.HBox([metric_dropdown, decade_dropdown]))
display(map)

# Initial map update
update_map(metrics[0], decades[0])

# %%
