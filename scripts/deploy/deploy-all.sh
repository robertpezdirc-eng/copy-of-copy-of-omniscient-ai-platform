#!/bin/bash
#
# Master deployment script for OMNI Platform
# Provides menu to deploy to different environments
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
   ____  __  __ _   _ ___   ____  _       _    __                      
  / __ \|  \/  | \ | |_ _| |  _ \| | __ _| |_ / _| ___  _ __ _ __ ___  
 | |  | | |\/| |  \| || |  | |_) | |/ _` | __| |_ / _ \| '__| '_ ` _ \ 
 | |  | | |  | | |\  || |  |  __/| | (_| | |_|  _| (_) | |  | | | | | |
  \____/|_|  |_|_| \_|___| |_|   |_|\__,_|\__|_|  \___/|_|  |_| |_| |_|
                                                                         
  Deployment Manager
EOF
echo -e "${NC}"

echo "Select deployment target:"
echo ""
echo "  1) 🐳 Docker (Local Development)"
echo "  2) ☁️  Google Cloud Run (Production)"
echo "  3) 🌐 GitHub Pages (Static Hosting)"
echo "  4) 🔍 Health Check (All Services)"
echo "  5) 📊 Show Status"
echo "  6) 🛑 Rollback Last Deployment"
echo "  7) ❌ Exit"
echo ""
read -p "Enter choice [1-7]: " choice

case $choice in
    1)
        echo -e "${YELLOW}🐳 Deploying to Docker...${NC}"
        ./deploy-docker.sh
        ;;
    2)
        echo -e "${YELLOW}☁️  Deploying to Google Cloud Run...${NC}"
        echo "⚠️  This will deploy to production!"
        read -p "Continue? (y/N): " confirm
        if [[ $confirm == [yY] ]]; then
            ./deploy-cloud-run.sh
        else
            echo "Deployment cancelled"
        fi
        ;;
    3)
        echo -e "${YELLOW}🌐 Deploying to GitHub Pages...${NC}"
        ./deploy-github-pages.sh
        ;;
    4)
        echo -e "${YELLOW}🔍 Running health checks...${NC}"
        ./health-check.sh
        ;;
    5)
        echo -e "${YELLOW}📊 Checking deployment status...${NC}"
        echo ""
        echo "Docker Services:"
        docker-compose ps 2>/dev/null || echo "  Not running"
        echo ""
        echo "Cloud Run Services:"
        gcloud run services list --region europe-west1 2>/dev/null || echo "  Not configured"
        ;;
    6)
        echo -e "${YELLOW}🛑 Rolling back...${NC}"
        ./rollback.sh
        ;;
    7)
        echo "Goodbye! 👋"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Operation completed successfully!${NC}"
