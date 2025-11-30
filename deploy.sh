#!/bin/bash

# School Portal - Quick Deploy Script for VPS
# This script automates the deployment process

set -e  # Exit on error

echo "================================================"
echo "School Portal - VPS Deployment Script"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}Please do not run as root${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Checking prerequisites...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker not found. Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}Docker installed successfully!${NC}"
else
    echo "Docker is already installed."
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Docker Compose not found. Installing...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}Docker Compose installed successfully!${NC}"
else
    echo "Docker Compose is already installed."
fi

echo ""
echo -e "${GREEN}Step 2: Setting up environment...${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    if [ -f ".env.production" ]; then
        cp .env.production .env
        echo "Created .env from .env.production"
        echo -e "${YELLOW}WARNING: Please edit .env file with your settings!${NC}"
        echo ""
        read -p "Press Enter to continue after editing .env file..."
    else
        echo -e "${RED}Error: .env.production not found!${NC}"
        exit 1
    fi
else
    echo ".env file already exists."
fi

# Prompt for domain (optional)
echo ""
read -p "Enter your domain name (or press Enter to skip): " DOMAIN

if [ ! -z "$DOMAIN" ]; then
    echo "Updating Nginx configuration for domain: $DOMAIN"
    sed -i "s/your-domain.com/$DOMAIN/g" nginx/conf.d/default.conf
    echo -e "${GREEN}Domain configured!${NC}"
fi

echo ""
echo -e "${GREEN}Step 3: Configuring firewall...${NC}"

# Set up UFW firewall
if command -v ufw &> /dev/null; then
    sudo ufw --force enable
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    echo -e "${GREEN}Firewall configured!${NC}"
else
    echo -e "${YELLOW}UFW not found. Please configure firewall manually.${NC}"
fi

echo ""
echo -e "${GREEN}Step 4: Building Docker containers...${NC}"
docker-compose build

echo ""
echo -e "${GREEN}Step 5: Starting services...${NC}"
docker-compose up -d

echo ""
echo "Waiting for services to start..."
sleep 15

echo ""
echo -e "${GREEN}Step 6: Running database migrations...${NC}"
docker-compose exec -T web python manage.py migrate

echo ""
echo -e "${GREEN}Step 7: Collecting static files...${NC}"
docker-compose exec -T web python manage.py collectstatic --noinput

echo ""
echo -e "${GREEN}Step 8: Creating superuser...${NC}"
echo "Please enter superuser credentials:"
docker-compose exec web python manage.py createsuperuser

echo ""
echo "================================================"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo "================================================"
echo ""
echo "Your School Portal is now running!"
echo ""
echo "Access your application:"
if [ ! -z "$DOMAIN" ]; then
    echo "  - API: https://$DOMAIN/api/"
    echo "  - Admin: https://$DOMAIN/admin/"
    echo "  - Swagger: https://$DOMAIN/swagger/"
else
    echo "  - API: http://localhost/api/"
    echo "  - Admin: http://localhost/admin/"
    echo "  - Swagger: http://localhost/swagger/"
fi
echo ""
echo "Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Restart services: docker-compose restart"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Set up SSL certificate (see VPS_DEPLOYMENT_GUIDE.md)"
echo "  2. Configure automated backups"
echo "  3. Test all functionality"
echo ""
echo "For detailed instructions, see VPS_DEPLOYMENT_GUIDE.md"
echo ""

