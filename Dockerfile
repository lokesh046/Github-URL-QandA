# ==========================================
# Stage 1: Build the React Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy source files and build
COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Build the FastAPI Backend
# ==========================================
FROM python:3.11-slim
WORKDIR /app/backend

# Install system dependencies (e.g., git, build essentials)
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY github_qa_bot/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY github_qa_bot/ ./

# Copy built frontend assets from Stage 1 into the backend's dist directory
COPY --from=frontend-builder /app/frontend/dist ./dist

# Create data cache directories (which will be mapped to a Render Persistent Volume)
RUN mkdir -p data/archives data/sha_cache data/graph_db

# Expose port and run the server
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
