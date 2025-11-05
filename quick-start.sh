#!/bin/bash
# WorkHub Quick Start Script
# This script will build and start the WorkHub application in Docker

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================"
echo -e "  WorkHub Task Management System"
echo -e "  Docker Quick Start"
echo -e "========================================${NC}"
echo ""

# Check if Docker is running
echo -e "${YELLOW}Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# Check if .env file exists
echo ""
echo -e "${YELLOW}Checking environment configuration...${NC}"
if [ ! -f .env ]; then
    echo -e "${GREEN}✓ Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}  Please edit .env file to configure your environment${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Build Docker images
echo ""
echo -e "${YELLOW}Building Docker images...${NC}"
echo -e "${GRAY}This may take a few minutes on first run...${NC}"
docker-compose build
echo -e "${GREEN}✓ Build completed successfully${NC}"

# Start containers
echo ""
echo -e "${YELLOW}Starting containers...${NC}"
docker-compose up -d
echo -e "${GREEN}✓ All containers started${NC}"

# Wait for services to be ready
echo ""
echo -e "${YELLOW}Waiting for services to initialize...${NC}"
sleep 5

# Check container status
echo ""
echo -e "${YELLOW}Checking container status...${NC}"
docker-compose ps

# Test backend health
echo ""
echo -e "${YELLOW}Testing backend API...${NC}"
sleep 3
if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${YELLOW}⚠ Backend is starting up... (this is normal)${NC}"
fi

# Display success message
echo ""
echo -e "${GREEN}========================================"
echo -e "  ✓ WorkHub is now running!"
echo -e "========================================${NC}"
echo ""
echo -e "${CYAN}Access the application:${NC}"
echo -e "  • Frontend: http://localhost:3000"
echo -e "  • Backend:  http://localhost:5000"
echo ""
echo -e "${CYAN}Default login credentials:${NC}"
echo -e "  • Username: admin"
echo -e "  • Password: admin123"
echo ""
echo -e "${YELLOW}⚠ Please change the admin password after first login!${NC}"
echo ""
echo -e "${CYAN}Useful commands:${NC}"
echo -e "${GRAY}  • View logs:    docker-compose logs -f${NC}"
echo -e "${GRAY}  • Stop:         docker-compose down${NC}"
echo -e "${GRAY}  • Restart:      docker-compose restart${NC}"
echo ""
echo -e "${GRAY}For more information, see DOCKER_DEPLOYMENT.md${NC}"
echo ""

# Open browser (Linux/Mac)
read -p "Open application in browser? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v xdg-open > /dev/null; then
        xdg-open http://localhost:3000
    elif command -v open > /dev/null; then
        open http://localhost:3000
    else
        echo "Please open http://localhost:3000 in your browser"
    fi
fi

