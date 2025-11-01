#!/bin/bash
#
# Deploy OMNI Platform to GitHub Pages
# Automatically builds and deploys the frontend to GitHub Pages
#

set -e

echo "🚀 OMNI Platform - GitHub Pages Deployment"
echo "=========================================="

# Configuration
REPO_NAME="copy-of-copy-of-omniscient-ai-platform"
BRANCH="gh-pages"
BUILD_DIR="dist"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

echo -e "${YELLOW}📦 Step 1: Preparing build directory${NC}"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

echo -e "${YELLOW}📋 Step 2: Copying frontend files${NC}"
cp -r frontend/* $BUILD_DIR/
cp -r frontend/modules $BUILD_DIR/ 2>/dev/null || true

echo -e "${YELLOW}🔧 Step 3: Updating configuration${NC}"
# Update env.js for production
cat > $BUILD_DIR/env.js << 'EOF'
window.ENV = {
    API_BASE_URL: 'https://backend-service-661612368188.europe-west1.run.app',
    AI_GATEWAY_URL: 'https://ai-gateway-661612368188.europe-west1.run.app'
};
EOF

echo -e "${YELLOW}📝 Step 4: Creating index redirect${NC}"
# Create root index.html that redirects to omni-dashboard
cat > $BUILD_DIR/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0;url=omni-dashboard.html">
    <title>OMNI Intelligence Platform</title>
</head>
<body>
    <p>Redirecting to <a href="omni-dashboard.html">OMNI Dashboard</a>...</p>
</body>
</html>
EOF

echo -e "${YELLOW}🌐 Step 5: Deploying to GitHub Pages${NC}"

# Initialize gh-pages branch if it doesn't exist
if ! git show-ref --verify --quiet refs/heads/$BRANCH; then
    echo "Creating $BRANCH branch..."
    git checkout --orphan $BRANCH
    git rm -rf .
    echo "# OMNI Platform - GitHub Pages" > README.md
    git add README.md
    git commit -m "Initialize GitHub Pages"
    git checkout -
fi

# Deploy to gh-pages
cd $BUILD_DIR
git init
git add -A
git commit -m "Deploy OMNI Platform - $(date '+%Y-%m-%d %H:%M:%S')"
git branch -M $BRANCH
git remote add origin git@github.com:robertpezdirc-eng/$REPO_NAME.git || true
git push -f origin $BRANCH

cd ..

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "📡 Your site will be available at:"
echo "   https://robertpezdirc-eng.github.io/$REPO_NAME/"
echo ""
echo "⏱️  Note: It may take a few minutes for changes to appear"
echo ""
echo "🔗 To enable GitHub Pages:"
echo "   1. Go to repository Settings"
echo "   2. Navigate to Pages section"
echo "   3. Select 'gh-pages' branch as source"
echo "   4. Click Save"
