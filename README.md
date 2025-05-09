# Unicef Geospatial Project

This project is a collection of tools and scripts for working with geospatial data and AI.
The objective is to research and develop tools for interacting with geospatial data using natural language.

### Architecture

![Architecture](architecture.png)

### Demo

https://github.com/user-attachments/assets/c4d4a8e6-a248-4231-b9dc-abbe9f13e11f

### Installing dependencies

This project is run using Docker and Docker Compose. Ensure you have Docker Desktop (or Docker Engine with the Compose plugin) installed on your system.
Docker will handle the installation of all necessary dependencies, including the Google Cloud CLI, as defined in the `Dockerfile` and `docker-compose.yml` files.

You will also need to set up the required secrets as detailed in the "Secrets" section below.

### Running the project

To build and run the entire project (API and frontend):

```bash
docker-compose up --build
```

This command will build the Docker images for the API and frontend if they don't exist or if `Dockerfile`s have changed.
You can add the -d flag to start the Docker images in the dettached mode.

The API will be available at `http://localhost:8000/` (or the port specified by `BACKEND_PORT_HOST` in your `.env` file if you've overridden the default).
The frontend will be available at `http://localhost:5173/` (or the port specified by `FRONTEND_PORT_HOST` in your `.env` file if you've overridden the default).

To stop the services:

```bash
docker-compose down
```

### Authentication

The application includes JWT authentication with predefined users. The users are saved in the `users.json` file insi.

There is a file example of the `users.json` in the `users_example.json` file.

Authentication can be enabled/disabled by setting the `VITE_AUTH_ENABLED` environment variable in the frontend's `.env` file.

### Secrets

The project uses a combination of a root `.env` file for general configuration and a `secrets` directory for sensitive files managed by Docker Compose.

First, copy the example `.env.example` file to a new file called `.env` in the project root:

```bash
cp .env.example .env
```

The `.env` file should be located in the root of the project and contain the following variables. This file is used by `docker-compose` to set environment variables for the services and is also copied into the API service image.

- `OPENAI_API_KEY`: The API key for OpenAI.
- `MODEL_NAME`: The name of the OpenAI model to use.
- `TEMPERATURE = 0.0`: The temperature of the agent.
- `LANGFUSE_PUBLIC_KEY`: The public key for the langfuse cloud.
- `LANGFUSE_SECRET_KEY`: The secret key for the langfuse cloud.
- `LANGFUSE_HOST`: The host URL for the langfuse cloud.
- `LANGFUSE_PROJECT_ID`: The project id for the langfuse cloud.
- `BACKEND_HOST`: The API host address (used by the application if needed, typically `0.0.0.0` inside Docker).
- `BACKEND_PORT`: The API port number (used by the application if needed, typically `8000` inside Docker).
- `BACKEND_PORT_HOST`: The host port to map to the backend container's port (default: 8000).
- `BACKEND_PORT_CONTAINER`: The backend container's internal port (default: 8000).
- `FRONTEND_PORT_HOST`: The host port to map to the frontend container's port (default: 5173).
- `FRONTEND_PORT_CONTAINER`: The frontend container's internal port (default: 5173).
- `RELOAD`: Whether to reload the API on change. Recommended for development environment.
- `PATH_TO_EE_AUTH`: Path to the Earth Engine authentication file. When running with Docker, set this to `/run/secrets/ee_auth_secret`.
- `JWT_SECRET_KEY`: Secret key for JWT token generation (required for authentication).
- `JWT_ALGORITHM`: Algorithm used for JWT token generation (default is HS256).
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiration time for JWT tokens in minutes.

**Docker Secrets Directory**

`docker-compose.yml` expects certain sensitive files to be present in a `./.secrets/` directory in the project root. Create this directory if it doesn't exist. There is a directory example with the needed secrets in the `./.secrets.example/` directory

```bash
cp -r .secrets.example ./secrets
```

The following files must be placed inside the `./secrets/` directory:

1.  **Earth Engine Authentication File**:
    The Google Earth Engine service account credentials file should be named `ee_auth.json` and placed in `./secrets/ee_auth.json`.
    It should look like this:

    ```json
    {
      "type": "service_account",
      "project_id": "XXX",
      "private_key_id": "XXX",
      "private_key": "XXX",
      "client_email": "XXX",
      "client_id": "XXX",
      "auth_uri": "XXX",
      "token_uri": "XXX",
      "auth_provider_x509_cert_url": "XXX",
      "client_x509_cert_url": "XXX",
      "universe_domain": "XXX"
    }
    ```

    Remember to set `PATH_TO_EE_AUTH=/run/secrets/ee_auth_secret` in your root `.env` file so the application can find this file inside the container.

2.  **User Definitions File**:
    The `users.json` file should be placed in `./.secrets/users.json`. This file is used for JWT authentication.

3.  **OpenAI API Key File**:
    Create a file named `openai_api_key.txt` in the `./.secrets/` directory. This file should contain your OpenAI API key as plain text.

    Ensure the `PATH_TO_LLM_API_KEY` variable is also set in your root `.env` file.

4.  **Langfuse Secret Key File**:
    Create a file named `langfuse_secret_key.txt` in the `./secrets/` directory. This file should contain your Langfuse secret key as plain text.
    Example: `./secrets/langfuse_secret_key.txt`
    ```
    yourLangfuseSecretKeyHere
    ```
    Ensure the `PATH_TO_LANGFUSE_SECRET_KEY` variable is also set in your root `.env` file.

**Frontend Environment Variables**

The frontend has its own `.env` file inside the `frontend` directory. Navigate to the `frontend` directory and copy the example:

```bash
cd frontend
cp .env.example .env
```

The frontend `.env` must include:

- `VITE_BACKEND_URL`: The URL of the backend API
- `VITE_HOST`: The host address for the frontend server
- `VITE_PORT`: The port number for the frontend server
- `VITE_AUTH_ENABLED`: Whether to enable authentication (true/false)

### Accessing the logs

The logs are stored in langfuse cloud. They are accesible [here](https://cloud.langfuse.com/organization/cm6gkfzm100dxo9t33ydvuyxw).

### Running the benchmark

To run the benchmark, after installing the dependencies, run the following command:

```bash
./benchmark.sh <n_workers>
```

This will log the results in langfuse cloud and create a local file named [`results.tsv`](results.tsv)

### Project structure

- `unicef_geospatial/`: The main project for working with geospatial data.

  - `agent/`: Functions for creating and running langchain agents.
  - `data_warehouse/`: Tools and functions for interacting with the unicef data warehouse.
  - `earth_engine/`: Functions for interacting with google earth engine.
  - `geospatial/`: Tools and functions for interacting with geospatial data.
  - `utils/`: Utility functions for the project.
  - `app.py`: The main entry point for the API.

- `unicef-frontend/`: The frontend for the project.

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
