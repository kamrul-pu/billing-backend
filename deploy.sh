#!/bin/bash

# Deployment script for Coolify
set -e

echo "🚀 Starting deployment process..."

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Please run this script from the project root."
    exit 1
fi

# Check if required files exist
required_files=("coolify.yml" "Dockerfile" "requirements/production.txt" "startup.sh")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Error: Required file $file not found."
        exit 1
    fi
done

echo "✅ All required files found."

# Make scripts executable
chmod +x startup.sh
chmod +x deploy.sh

echo "✅ Scripts made executable."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Please create one based on env.production"
    echo "   You can copy env.production to .env and update the values."
fi

echo "🔧 Building Docker image..."
docker build -t billing-backend:latest .

echo "✅ Docker image built successfully."

echo "🐳 Starting services with docker-compose..."
docker-compose -f coolify.yml up -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "🔍 Checking service health..."
# Check if web service is responding
if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
    echo "✅ Web service is healthy"
else
    echo "❌ Web service health check failed"
    echo "📋 Checking logs..."
    docker-compose -f coolify.yml logs web
fi

echo "📊 Service status:"
docker-compose -f coolify.yml ps

echo "🎉 Deployment completed!"
echo ""
echo "📝 Next steps:"
echo "1. Configure your domain in Coolify"
echo "2. Set up SSL certificates"
echo "3. Configure your database connection"
echo "4. Update environment variables"
echo ""
echo "🔗 Access your application:"
echo "- Web: http://localhost:8000"
echo "- Health: http://localhost:8000/health/"
echo "- Admin: http://localhost:8000/admin/"
echo ""
echo "📋 Useful commands:"
echo "- View logs: docker-compose -f coolify.yml logs -f"
echo "- Stop services: docker-compose -f coolify.yml down"
echo "- Restart services: docker-compose -f coolify.yml restart"
