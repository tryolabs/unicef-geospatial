from pathlib import Path

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from logging_config import get_logger
from utils.initialize import initialize_earth_engine


class AppState:
    def __init__(self):
        self.app = FastAPI()
        self.params = self._load_params()
        self.logger = get_logger(__name__)
        self.templates = self._init_app()

    def _load_params(self) -> dict:
        """Load parameters from YAML file."""
        params_path = Path("unicef_geospatial/params.yaml")
        with params_path.open("r") as f:
            return yaml.safe_load(f)

    def _init_app(self) -> Jinja2Templates:
        """Initialize application components."""
        # Mount static files
        self.app.mount(
            "/static",
            StaticFiles(directory="unicef_geospatial/frontend/static"),
            name="static",
        )

        load_dotenv(override=True)
        self.logger.info("Loading application with project")

        # Initialize components
        initialize_earth_engine(self.params["auth"]["path_to_ee_auth"])

        # Mount templates
        return Jinja2Templates(directory="unicef_geospatial/frontend/templates")
