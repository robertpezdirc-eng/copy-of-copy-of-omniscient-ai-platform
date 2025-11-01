#!/bin/bash
#
# Rollback script for OMNI Platform
# Reverts to previous deployment
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔄 OMNI Platform - Rollback"
echo "==========================="
echo ""

echo "Select environment to rollback:"
echo "  1) Docker (restart previous version)"
echo "  2) Cloud Run (revert to previous revision)"
echo "  3) Cancel"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo -e "${YELLOW}🐳 Rolling back Docker deployment...${NC}"
        docker-compose down
        # Pull previous images
        docker-compose pull
        docker-compose up -d
        echo -e "${GREEN}✅ Docker rollback complete${NC}"
        ;;
    2)
        echo -e "${YELLOW}☁️  Rolling back Cloud Run deployment...${NC}"
        
        # Rollback frontend
        echo "Rolling back frontend..."
        gcloud run services update-traffic omni-frontend \
            --to-revisions=LATEST=0,previous=100 \
            --region europe-west1
        
        # Rollback backend  
        echo "Rolling back backend..."
        gcloud run services update-traffic omni-backend \
            --to-revisions=LATEST=0,previous=100 \
            --region europe-west1
        
        echo -e "${GREEN}✅ Cloud Run rollback complete${NC}"
        ;;
    3)
        echo "Rollback cancelled"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "🔍 Running health check..."
./health-check.sh
