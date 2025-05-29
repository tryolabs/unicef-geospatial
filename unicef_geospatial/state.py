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

        with open(os.getenv("PATH_TO_LANGFUSE_SECRET_KEY"), "r") as f:
            os.environ["LANGFUSE_SECRET_KEY"] = f.read().strip()

        with open(os.getenv("PATH_TO_LLM_API_KEY"), "r") as f:
            os.environ["OPENAI_API_KEY"] = f.read().strip()

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
            frontend_origins = os.getenv("FRONTEND_ORIGIN", "").split(",")
            allowed_hostnames_ips = []

            if frontend_origins:
                for origin_url_str in frontend_origins:
                    parsed_url = urlparse(origin_url_str.strip())
                    hostname = parsed_url.hostname
                    if hostname:
                        allowed_hostnames_ips.append(hostname)
                        try:
                            ip_address = socket.gethostbyname(hostname)
                            if ip_address not in allowed_hostnames_ips:
                                allowed_hostnames_ips.append(ip_address)
                        except socket.gaierror:
                            self.logger.warning(
                                f"Could not resolve hostname: {hostname} from FRONTEND_ORIGIN"
                            )

            if "localhost" not in allowed_hostnames_ips:
                allowed_hostnames_ips.append("localhost")
            if "testclient" not in allowed_hostnames_ips:
                allowed_hostnames_ips.append("testclient")

            client_ip = request.client.host if request.client else None

            # Check if client IP is in allowed list
            if client_ip not in allowed_hostnames_ips:
                self.logger.warning(
                    f"Blocked request from unauthorized IP/hostname: {client_ip}. Allowed: {allowed_hostnames_ips}"
                )
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Access denied from this IP address"},
                )

            return await call_next(request)

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=os.getenv("FRONTEND_ORIGIN").split(","),
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
        )
