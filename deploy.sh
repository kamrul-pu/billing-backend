#!/bin/bash

# Deployment script for Coolify
# This script helps with local testing and preparation for deployment

set -e

echo "🚀 Billing Backend Deployment Script"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from template..."
    if [ -f "env.production.example" ]; then
        cp env.production.example .env
        print_status "Created .env from template. Please update the values."
    else
        print_error "env.production.example not found. Please create .env manually."
        exit 1
    fi
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build the Docker image
print_status "Building Docker image..."
docker build -t billing-backend:latest .

if [ $? -eq 0 ]; then
    print_status "Docker image built successfully!"
else
    print_error "Failed to build Docker image."
    exit 1
fi

# Test the container locally (optional)
if [ "$1" = "--test" ]; then
    print_status "Testing container locally..."
    
    # Stop existing containers
    docker-compose down 2>/dev/null || true
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    sleep 10
    
    # Test health endpoint
    if curl -f http://localhost/health/ > /dev/null 2>&1; then
        print_status "✅ Health check passed! Application is running."
        print_status "🌐 Application URL: http://localhost"
        print_status "📊 Health check: http://localhost/health/"
        print_status "🔧 Admin panel: http://localhost/admin/"
        print_status "📚 API docs: http://localhost/api/docs/"
    else
        print_error "❌ Health check failed. Check the logs:"
        docker-compose logs
        exit 1
    fi
    
    print_warning "To stop the test environment, run: docker-compose down"
fi

print_status "Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. Update your .env file with production values"
echo "2. Push your code to your Git repository"
echo "3. Deploy using Coolify following the COOLIFY_DEPLOYMENT.md guide"
echo ""
echo "For local testing, run: ./deploy.sh --test"
