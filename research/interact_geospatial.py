# %%
import time
from typing import Literal

import ee
import pycountry
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_cohere import ChatCohere
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent

load_dotenv(override=True)

ee.Authenticate()
ee.Initialize(project="unicef-geospatial")

METRICS = Literal["frequency", "duration", "severity", "extreme_high_temp"]
DECADES = Literal["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
COUNTRY_BOUNDRIES_DATASET = "USDOS/LSIB_SIMPLE/2017"
REDUCERS = Literal["mean", "max", "min"]


# %%
def print_stream(stream: list) -> None:
    """Print messages from a stream of LangChain agent responses."""
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()


def standarize_country_name(country: str) -> str:
    """Return the official country name using the input."""
    try:
        country_obj = (
            pycountry.countries.get(name=country)
            or pycountry.countries.get(alpha_2=country)
            or pycountry.countries.get(alpha_3=country)
        )
        if country_obj:
            return country_obj.name
        else:
            return country
    except KeyError:
        return country


@tool
def get_heatwave_metric_for_country(
    metric: METRICS, decade: DECADES, country: str, reducer: REDUCERS = "mean"
) -> dict:
    """Get the value of a heatwave metric for a specific country and decade.

    Args:
        metric: One of 'frequency', 'duration', 'severity', 'extreme_high_temp'
        decade: One of '1960s', '1970s', '1980s', '1990s', '2000s', '2010s', '2020s'
        country: Name of the country
        reducer: The reducer to use ('mean', 'max', 'min', etc). Defaults to 'mean'

    Returns:
        The value of the heatwave metric for the specified country and decade.
    """
    country = standarize_country_name(country)
    heatwave_tiff = ee.Image(
        f"projects/unicef-geospatial/assets/heatwaves/{metric}/average_heatwaves_{metric}_{decade}_proj_COG"
    )
    countries_boundries = ee.FeatureCollection(COUNTRY_BOUNDRIES_DATASET)

    country_boundries = countries_boundries.filter(ee.Filter.eq("country_na", country))
    country_heatwave = heatwave_tiff.clip(country_boundries)
    stats = country_heatwave.reduceRegion(
        reducer=getattr(ee.Reducer, reducer)(),
        geometry=country_boundries.geometry(),
        scale=1000,
        maxPixels=1e13,
    )
    return round(stats.getInfo()["b1"], 3)


# %%
# Initialize LLM and create agent
llm = ChatCohere(temperature=0.0)
tools = [get_heatwave_metric_for_country]

system_prompt = """You are an expert in analyzing heatwave data across different countries and time periods. 

You have access to a tool that can retrieve the value of a heatwave metric for a specific country and decade.
The available metrics are:
- frequency: How often heatwaves occur
- duration: Average length of heatwave event (Number of days).
- severity: Average exceedance in degrees Celsius of the heatwave threshold for each event.
- extreme_high_temp: Annual average number of days in which 35°C is exceeded.

You can analyze data from the 1960s through the 2020s. When users ask questions, make sure to:
1. Identify the correct metric they're asking about
2. Determine the relevant decade
3. Properly identify the country name
4. Use the tool to fetch the data and specify if you want the mean, max, or min value
5. Return the response saying something like but using the same language as the user's question:

"The _reducer_ value of the heatwave _metric_ for _country_ in the _decade_ is _value_"
"""

graph = create_react_agent(
    tools=tools,
    model=llm,
    state_modifier=system_prompt,
)


# %%
inputs = {
    "messages": [
        {
            "role": "user",
            "content": "What was the average duration of heatwaves in Uy in the 1990s?",
        }
    ]
}
res = graph.invoke(inputs)
print_stream(graph.stream(inputs, stream_mode="values"))
# %%
