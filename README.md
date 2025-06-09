# Unicef Geospatial Project

This project is a collection of tools and scripts for working with geospatial data and AI.
The objective is to research and develop tools for interacting with geospatial data using natural language.

### Architecture

![Architecture](architecture.png)

### Demo

https://github.com/user-attachments/assets/c4d4a8e6-a248-4231-b9dc-abbe9f13e11f

### Installing dependencies

This project is run using Docker and Docker Compose. Ensure you have Docker installed on your system. Docker will handle the installation of all necessary dependencies

You will also need to set up the required secrets as detailed in the "Secrets" section below.

To install the dependencies for running specifically the api for the benchmark or tests, installing [uv](https://docs.astral.sh/uv/guides/install-python/) and [Google CLI](https://cloud.google.com/sdk/docs/install) is necessary

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

### Secrets

The project uses a combination of a root `.env` file for general configuration and a `secrets` directory for sensitive files managed by Docker Compose.

**Docker Secrets Directory**

`docker-compose.yml` expects certain sensitive files to be present in a `./.secrets/` directory in the project root. Create this directory if it doesn't exist. There is a directory example with the needed secrets in the `./.secrets.example/` directory

```bash
cp -r .secrets.example ./.secrets
```

The following files must be placed inside the `./.secrets/` directory:

1.  **Earth Engine Authentication File**:
    The Google Earth Engine service account credentials file should be named `ee_auth.json` and placed in `./.secrets/ee_auth.json`.
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
    The `users.json` file should be placed in `./.secrets/users.json`. This file is used for JWT authentication, and should have pairs of `username`, `hashed_password`.

3.  **OpenAI API Key File**:
    Create a file named `openai_api_key.txt` in the `./.secrets/` directory. This file should contain your OpenAI API key as plain text.

    Ensure the `PATH_TO_LLM_API_KEY` variable is also set in your root `.env` file.

4.  **Langfuse Secret Key File**:
    Create a file named `langfuse_secret_key.txt` in the `./.secrets/` directory. This file should contain your Langfuse secret key as plain text.
    Example: `./.secrets/langfuse_secret_key.txt`
    ```
    yourLangfuseSecretKeyHere
    ```
    Ensure the `PATH_TO_LANGFUSE_SECRET_KEY` variable is also set in your root `.env` file.

Then, copy the example `.env.example` file to a new file called `.env` in the project root:

```bash
cp .env.example .env
```

The `.env` file should be located in the root of the project and contain the following variables. This file is used by `docker-compose` to set environment variables for the services and is also copied into the API service image.

- `PATH_TO_LLM_API_KEY`: The path to the secret API key.
- `MODEL_NAME`: The name of the OpenAI model to use.
- `TEMPERATURE`: The temperature of the agent.
- `LANGFUSE_PUBLIC_KEY`: The public key for the langfuse cloud.
- `PATH_TO_LANGFUSE_SECRET_KEY`: The path to the secret key for the langfuse cloud.
- `LANGFUSE_HOST`: The host URL for the langfuse cloud.
- `LANGFUSE_PROJECT_ID`: The project id for the langfuse cloud.
- `BACKEND_HOST`: The API host address.
- `BACKEND_PORT`: The API port number.
- `BACKEND_PORT_HOST`: The host port to map to the backend container's port.
- `BACKEND_PORT_CONTAINER`: The backend container's internal port.
- `RELOAD`: Whether to reload the API on change. Recommended for development environment.
- `FRONTEND_ORIGIN`: Allowed frontend origins.
- `PATH_TO_EE_AUTH`: Path to the Earth Engine authentication file. When running with Docker, set this to `/run/secrets/ee_auth_secret`.
- `JWT_SECRET_KEY`: Secret key for JWT token generation (required for authentication).
- `JWT_ALGORITHM`: Algorithm used for JWT token generation (default is HS256).
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiration time for JWT tokens in minutes.
- `PATH_TO_USERS_FILE`: The path to the secret users file.

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

### Authentication

The application includes JWT authentication with predefined users. The users are saved in the `users.json` file insi.

There is a file example of the `users.json` in the `users_example.json` file.

Authentication can be enabled/disabled by setting the `VITE_AUTH_ENABLED` environment variable in the frontend's `.env` file.

### Processing CCRI 2025 Technical Documentation

To process the document of the technical documentation, run the script `process_ccri_doc.py`:

```bash
uv run python unicef_geospatial/process_ccri_doc.py
```

### Accessing the logs

The logs are stored in langfuse cloud. They are accesible [here](https://cloud.langfuse.com/organization/cm6gkfzm100dxo9t33ydvuyxw).

### Running the benchmark

To run the benchmark, after installing the dependencies, run the following command:

```bash
./benchmark.sh <n_workers>
```

This will log the results in langfuse cloud and create a local file named [`results.tsv`](results.tsv)

### Running the tests

To run the tests:

```
uv run python tests/test_runner.py all
```

### Project structure

- `unicef_geospatial/`: The main project for working with geospatial data.

  - `agent/`: Functions for creating and running langchain agents.
  - `data_warehouse/`: Tools and functions for interacting with the unicef data warehouse.
  - `geospatial/`: Tools and functions for interacting with geospatial data.
  - `utils/`: Utility functions for the project.
  - `app.py`: The main entry point for the API.

- `unicef-frontend/`: The frontend for the project.

- `notebooks/`: Notebooks with interactive visualizations and demonstrations.
- `research/`: Research scripts for exploring geospatial data, unicef api, etc.
