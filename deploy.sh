#!/bin/bash

# Work Hub Production Deployment Script
# This script deploys the Work Hub application to production

set -e

echo "🚀 Starting Work Hub Production Deployment..."

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "❌ Error: .env.prod file not found!"
    echo "Please copy .env.prod.example to .env.prod and configure your environment variables."
    exit 1
fi

# Load environment variables
export $(cat .env.prod | grep -v '^#' | xargs)

# Check required environment variables
required_vars=("MYSQL_ROOT_PASSWORD" "MYSQL_DATABASE" "MYSQL_USER" "MYSQL_PASSWORD" "SECRET_KEY" "JWT_SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set!"
        exit 1
    fi
done

echo "✅ Environment variables validated"

# Create SSL directory if it doesn't exist
mkdir -p nginx/ssl

# Check if SSL certificates exist
if [ ! -f nginx/ssl/cert.pem ] || [ ! -f nginx/ssl/key.pem ]; then
    echo "⚠️  Warning: SSL certificates not found in nginx/ssl/"
    echo "Please add your SSL certificates:"
    echo "  - nginx/ssl/cert.pem"
    echo "  - nginx/ssl/key.pem"
    echo ""
    echo "For testing, you can generate self-signed certificates:"
    echo "  openssl req -x509 -newkey rsa:4096 -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem -days 365 -nodes"
    read -p "Do you want to continue without SSL certificates? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down || true

# Build and start services
echo "🔨 Building and starting services..."
docker-compose -f docker-compose.prod.yml up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check if services are running
echo "🔍 Checking service health..."

# Check MySQL
if ! docker-compose -f docker-compose.prod.yml exec mysql mysqladmin ping -h localhost --silent; then
    echo "❌ MySQL is not healthy"
    exit 1
fi

# Check Backend
if ! curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "❌ Backend is not healthy"
    exit 1
fi

# Check Frontend
if ! curl -f http://localhost:80/health > /dev/null 2>&1; then
    echo "❌ Frontend is not healthy"
    exit 1
fi

echo "✅ All services are healthy!"

# Initialize database
echo "🗄️  Initializing database..."
docker-compose -f docker-compose.prod.yml exec backend python init_db.py

echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Service URLs:"
echo "  Frontend: http://localhost:80"
echo "  Backend API: http://localhost:5000/api"
echo "  Health Check: http://localhost:80/health"
echo ""
echo "🔐 Default Admin Credentials:"
echo "  Email: admin@workhub.com"
echo "  Password: admin123"
echo ""
echo "⚠️  Remember to:"
echo "  1. Change default admin password"
echo "  2. Configure proper SSL certificates"
echo "  3. Update DNS records to point to your server"
echo "  4. Configure firewall rules"
echo "  5. Set up regular backups"
echo ""
echo "📊 To view logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"