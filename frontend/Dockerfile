# Stage 1: Build the frontend
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package.json package-lock.json* ./

# Install dependencies
# Using npm ci for cleaner installs based on lock file
RUN npm ci

# Copy the rest of the application code
COPY . .

# Build the application in two steps for better error visibility
# First, run TypeScript compilation using npx to ensure it uses the local version
RUN npx tsc -b
# Then, run Vite build, also with npx for consistency if vite is a local dep
RUN npx vite build

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

# Copy built assets from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
# We'll create a simple nginx.conf next to handle SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose the port the app runs on (default 5173 from VITE_PORT)
EXPOSE 5173

# Start Nginx
CMD ["nginx", "-g", "daemon off;"] 