#!/bin/bash

# Railway Quick Deploy Script for Armor of God Church Backend
# This script helps you quickly deploy to Railway

echo "🚂 Railway Deployment Script - Armor of God Church Backend"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not found!${NC}"
    echo ""
    echo "Install Railway CLI:"
    echo "  npm install -g @railway/cli"
    echo ""
    echo "Or visit: https://docs.railway.app/develop/cli"
    exit 1
fi

echo -e "${GREEN}✅ Railway CLI found${NC}"
echo ""

# Check if logged in
echo "Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Railway${NC}"
    echo ""
    echo "Logging in..."
    railway login
else
    echo -e "${GREEN}✅ Already logged in to Railway${NC}"
fi

echo ""
echo "============================================================"
echo "📦 Pre-deployment Checklist"
echo "============================================================"
echo ""

# Check for required files
files=("requirements.txt" "Procfile" "app.py" "runtime.txt")
all_files_present=true

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} $file"
    else
        echo -e "${RED}❌${NC} $file - MISSING!"
        all_files_present=false
    fi
done

if [ "$all_files_present" = false ]; then
    echo ""
    echo -e "${RED}❌ Some required files are missing!${NC}"
    echo "Please ensure all files are present before deploying."
    exit 1
fi

echo ""
echo "============================================================"
echo "🔧 Environment Variables Required"
echo "============================================================"
echo ""
echo "Make sure you have these ready:"
echo "  1. MONGO_URI - Your MongoDB Atlas connection string"
echo "  2. JWT_SECRET_KEY - A secure random string"
echo "  3. FLASK_ENV - Set to 'production'"
echo ""

read -p "Have you prepared all environment variables? (y/n): " confirm
if [[ $confirm != [yY] ]]; then
    echo ""
    echo -e "${YELLOW}⚠️  Please prepare your environment variables first.${NC}"
    echo ""
    echo "To generate a secure JWT_SECRET_KEY:"
    echo "  python -c \"import secrets; print(secrets.token_hex(32))\""
    echo ""
    exit 1
fi

echo ""
echo "============================================================"
echo "🚀 Deployment Options"
echo "============================================================"
echo ""
echo "1. Initialize new Railway project"
echo "2. Link to existing Railway project"
echo "3. Deploy to current project"
echo "4. Exit"
echo ""

read -p "Choose an option (1-4): " option

case $option in
    1)
        echo ""
        echo "Initializing new Railway project..."
        railway init
        echo ""
        echo -e "${GREEN}✅ Project initialized${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Add environment variables: railway variables"
        echo "  2. Deploy: railway up"
        ;;
    2)
        echo ""
        echo "Linking to existing project..."
        railway link
        echo ""
        echo -e "${GREEN}✅ Project linked${NC}"
        ;;
    3)
        echo ""
        echo "Deploying to Railway..."
        railway up
        echo ""
        echo -e "${GREEN}✅ Deployment complete!${NC}"
        echo ""
        echo "View your deployment:"
        echo "  railway open"
        echo ""
        echo "View logs:"
        echo "  railway logs"
        ;;
    4)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

echo ""
echo "============================================================"
echo "📊 Useful Railway Commands"
echo "============================================================"
echo ""
echo "View logs:           railway logs"
echo "Open dashboard:      railway open"
echo "Set variables:       railway variables"
echo "View project info:   railway status"
echo "Run locally:         railway run python app.py"
echo ""
echo -e "${GREEN}✅ Deployment process complete!${NC}"
echo ""