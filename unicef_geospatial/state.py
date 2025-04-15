import os
import socket
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from logging_config import get_logger
from utils.constants import BASE_PATH
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

        if not os.path.exists(BASE_PATH):
            self.logger.info("Creating directory %s", BASE_PATH)
            os.makedirs(BASE_PATH)

            # IP Filtering Middleware to only allow requests from the frontend server

        @self.app.middleware("http")
        async def ip_filter_middleware(request: Request, call_next):
            frontend_origin = os.getenv("FRONTEND_ORIGIN", "")
            frontend_ip = None

            # Parse the frontend origin to extract the hostname
            if frontend_origin:
                parsed_url = urlparse(frontend_origin)
                hostname = parsed_url.hostname

                if hostname:
                    # Resolve hostname to IP
                    try:
                        frontend_ip = socket.gethostbyname(hostname)
                    except socket.gaierror:
                        self.logger.warning(f"Could not resolve hostname: {hostname}")

            # Always allow localhost for development
            allowed_ips = ["127.0.0.1", "localhost"]
            if frontend_ip:
                allowed_ips.append(frontend_ip)

            client_ip = request.client.host if request.client else None

            # Check if client IP is in allowed list
            if client_ip not in allowed_ips:
                self.logger.warning(
                    f"Blocked request from unauthorized IP: {client_ip}"
                )
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Access denied from this IP address"},
                )

            return await call_next(request)

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[os.getenv("FRONTEND_ORIGIN")],
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
        )
