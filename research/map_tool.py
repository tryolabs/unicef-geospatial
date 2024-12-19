# %%
import ee
import geemap.foliumap as geemap
from dotenv import load_dotenv
from IPython.display import display
from langchain.tools import tool
from langchain_cohere import ChatCohere
from langgraph.prebuilt import create_react_agent

load_dotenv(override=True)

ee.Authenticate()
ee.Initialize(project="unicef-geospatial")


# %%
@tool
def get_country_map(country: str) -> geemap.Map:
    """Returns a map of the country."""
    country_boundries = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
    uruguay_boundries = country_boundries.filter(ee.Filter.eq("country_na", country))

    country_map = geemap.Map()
    country_map.center_object(uruguay_boundries)
    country_map.add_layer(uruguay_boundries, {}, f"{country} Boundaries")
    return country_map


# %%
llm = ChatCohere(temperature=0.0)

graph = create_react_agent(
    llm,
    tools=[get_country_map],
)
# %%
inputs = {
    "messages": [
        {
            "role": "user",
            "content": "Get a map of Uruguay",
        }
    ]
}
graph.invoke(inputs)


# %%
