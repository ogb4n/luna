#!/bin/bash

# Docker optimization script for Luna Voice Bot

echo "🚀 Optimizing Docker setup for Luna Voice Bot..."

# Build optimized image
echo "📦 Building optimized Docker image..."
docker-compose build --no-cache --compress

# Remove unused images and containers
echo "🧹 Cleaning up unused Docker resources..."
docker system prune -f

# Show image size
echo "📊 Image size information:"
docker images | grep luna

# Show layer information
echo "🔍 Docker image layers:"
docker history $(docker images -q | head -1) --human --format "table {{.CreatedBy}}\t{{.Size}}"

echo "✅ Optimization complete!"
echo ""
echo "Usage commands:"
echo "  make run      - Start the bot"
echo "  make logs     - View logs"
echo "  make stop     - Stop the bot"
echo "  make dev-run  - Development mode"
