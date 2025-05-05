#!/bin/bash

# Get the number of workers from command line argument, default to 12 if not provided
WORKERS=${1:-12}

# Remove existing session ID to create a fresh one for this benchmark run
rm tests/results/.session_id

# Run the benchmark tests with the specified number of parallel workers
uv run pytest tests/run_benchmark.py -n $WORKERS
