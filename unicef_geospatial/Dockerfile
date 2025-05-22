FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install git, uv, Node.js, npm (needed for geemap), and Google Cloud CLI
RUN apt-get update && \
    apt-get install -y git nodejs npm curl gnupg apt-transport-https ca-certificates && \
    echo "deb [signed-by=/usr/share/keyrings/google-cloud-cli-archive-keyring.gpg] https://packages.cloud.google.com/apt cloud-sdk main" > /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/google-cloud-cli-archive-keyring.gpg && \
    apt-get update && \
    apt-get install -y google-cloud-cli && \
    pip install uv && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock /app/

RUN cd /app && uv sync && cd ..

COPY ./unicef_geospatial /app/unicef_geospatial
COPY ./run.py /app/run.py

COPY ./.env /app/.env

# Expose the port the app runs on
# Defaulting to 8000 as per run.py and .env.example
EXPOSE ${BACKEND_PORT:-8000}

# Set the default command to run the application using uv run
CMD ["uv", "run", "python", "run.py"] 