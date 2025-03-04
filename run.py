import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "unicef_geospatial"))
)

import uvicorn

if __name__ == "__main__":
    host = os.getenv("BACKEND_HOST", "localhost")
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("app:app", host=host, port=port, reload=True)
