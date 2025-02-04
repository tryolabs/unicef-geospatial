from pathlib import Path

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from logging_config import get_logger
from utils.initialize import initialize_earth_engine


class AppState:
    def __init__(self):
        self.app = FastAPI()
        self.params = self._load_params()
        self.logger = get_logger(__name__)

        self._init_app()

    def _load_params(self) -> dict:
        """Load parameters from YAML file."""
        params_path = Path("unicef_geospatial/params.yaml")
        with params_path.open("r") as f:
            return yaml.safe_load(f)

    def _init_app(self) -> None:
        """Initialize application components."""
        load_dotenv(override=True)
        self.logger.info("Loading application with project")

        # Initialize components
        initialize_earth_engine(self.params["auth"]["path_to_ee_auth"])

        # TODO: properly setup this
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allows all origins
            allow_credentials=True,
            allow_methods=["*"],  # Allows all methods
            allow_headers=["*"],  # Allows all headers
        )
