## Unicef Geospatial Project

This project is a collection of tools and scripts for working with geospatial data and AI.
The objective is to research and develop tools for interacting with geospatial data using natural language.

### Installing dependencies

The project dependencies are managed using `uv`.

### Running the project

To run the project, use the following command:

```bash
uv run python unicef_geospatial/app.py
```

This will start a local server at `http://127.0.0.1:8000/`.

### Project structure

- `unicef_geospatial/`: The main project for working with geospatial data.

  - `agent/`: Functions for creating and running langchain agents.
  - `data_warehouse/`: Tools and functions for interacting with the unicef data warehouse.
  - `earth_engine/`: Functions for interacting with google earth engine.
  - `geospatial/`: Tools and functions for interacting with geospatial data.
  - `frontend/`: The HTML, js and css for the frontend.
  - `utils/`: Utility functions for the project.
  - `app.py`: The main entry point for the API.

- `notebooks/`: Notebooks with interactive visualizations and demonstrations.
- `research/`: Research scripts for exploring geospatial data, unicef api, etc.

#### Notebooks

- `interactive_map.ipynb`: Ask questions in natural language about heatwave data.

#### Research

- `api_research.py`: Research on the unicef api, transform the sdmx-json to pandas dataframe.
- `ee_upload_images.py`: Upload heatwave data to google earth engine.
- `initial_research.py`: Research on how to use langchain agents to interact with a dataframe.
- `interact_geospatial.py`: Research on how to use langchain agents to interact with a geospatial data.
- `pandas_ai.py`: Research on how to use pandas-ai to interact with a unicef dataframe.
- `unicef_geospatial_ee.py`: Research on how to use google earth engine to interact with a geospatial data, creating an interactive map.
