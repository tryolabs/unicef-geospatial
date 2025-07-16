#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Setup ---
echo "Creating docker-images directory..."
mkdir -p docker-images

# --- Frontend ---
echo "Building and saving frontend image..."
(cd ./unicef-frontend && docker buildx build --platform linux/amd64 -t unicef-geospatial-frontend:latest --load .)
docker save -o docker-images/frontend.tar unicef-geospatial-frontend

# --- Agent ---
echo "Building and saving agent image..."
(cd ./unicef-agent && docker buildx build --platform linux/amd64 -t unicef-geospatial-agent:latest --load .)
docker save -o docker-images/agent.tar unicef-geospatial-agent

# --- Data-Warehouse MCP ---
echo "Building and saving datawarehouse_mcp image..."
(cd ./unicef-datawarehouse-mcp && docker buildx build --platform linux/amd64 -t unicef-geospatial-datawarehouse_mcp:latest --load .)
docker save -o docker-images/datawarehouse_mcp.tar unicef-geospatial-datawarehouse_mcp

# --- RAG MCP ---
echo "Building and saving rag_mcp image..."
(cd ./unicef-rag-mcp && docker buildx build --platform linux/amd64 -t unicef-geospatial-rag_mcp:latest --load .)
docker save -o docker-images/rag_mcp.tar unicef-geospatial-rag_mcp

# --- Geospatial MCP (GEE) ---
echo "Building and saving geospatial_mcp image..."
(cd ./unicef-gee-mcp && docker buildx build --platform linux/amd64 -t unicef-geospatial-geospatial_mcp:latest --load .)
docker save -o docker-images/geospatial_mcp.tar unicef-geospatial-geospatial_mcp

echo "✅ All images have been built for linux/amd64 and saved in the docker-images/ directory."
