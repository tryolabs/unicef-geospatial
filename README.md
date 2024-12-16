## Unicef Geospatial Project

This project is a collection of tools and scripts for working with geospatial data and AI.
The objective is to research and develop tools for interacting with geospatial data using natural language.

### Installing dependencies

The project dependencies are managed using `poetry`.

```bash
poetry install
```

### Running the project

First, initalize the poetry environment.

```bash
poetry shell
```

Then, run the project.

```bash
python -m unicef_geospatial.app
```

This will start a local server at `http://127.0.0.1:8000/`.

### Project structure

- `unicef_geospatial/`: The main project for working with geospatial data.
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
