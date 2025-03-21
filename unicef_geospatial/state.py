import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from logging_config import get_logger
from utils.initialize import initialize_earth_engine


class AppState:
    def __init__(self):
        self.app = FastAPI()
        self.logger = get_logger(__name__)

        self._init_app()

    def _init_app(self) -> None:
        """Initialize application components."""
        self.logger.info("Loading application with project")

        # Initialize components
        initialize_earth_engine(os.getenv("PATH_TO_EE_AUTH"))

        # TODO: properly setup this
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allows all origins
            allow_credentials=True,
            allow_methods=["*"],  # Allows all methods
            allow_headers=["*"],  # Allows all headers
        )
