#!/bin/bash

echo "=================================="
echo "Work Hub Setup Script"
echo "=================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Create .env file for backend if it doesn't exist
if [ ! -f workhub-backend/.env ]; then
    echo "📝 Creating backend .env file..."
    cp workhub-backend/.env.example workhub-backend/.env
    echo "✅ Backend .env file created. Please update it with your credentials."
else
    echo "ℹ️  Backend .env file already exists"
fi

echo ""
echo "🚀 Starting Work Hub with Docker Compose..."
echo ""

# Build and start containers
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 15

echo ""
echo "=================================="
echo "✅ Work Hub is now running!"
echo "=================================="
echo ""
echo "🌐 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:5000/api"
echo ""
echo "👤 Demo Login Credentials:"
echo "   Admin: admin@workhub.com / admin123"
echo "   User 1: john@workhub.com / user123"
echo "   User 2: jane@workhub.com / user123"
echo ""
echo "📋 Useful Commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop: docker-compose down"
echo "   Restart: docker-compose restart"
echo ""