#!/bin/bash

# =============================
# Django Deployment Script for PythonAnywhere
# Author: OA Wisdom Digital Firm
# =============================

# Define paths
PROJECT_DIR=~/NAG
WEBAPP_NAME="newafricagroup.pythonanywhere.com"

# Add colors for readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting automated deployment for $WEBAPP_NAME...${NC}"

# Step 1: Navigate to project directory
cd "$PROJECT_DIR" || { echo -e "${RED}❌ Project directory not found!${NC}"; exit 1; }

# Step 2: Clean and pull latest code
echo -e "${YELLOW}📦 Pulling latest code from GitHub...${NC}"
git reset --hard HEAD
git clean -fd
if git pull origin main; then
    echo -e "${GREEN}✅ Code updated successfully.${NC}"
else
    echo -e "${RED}❌ Git pull failed!${NC}"
    exit 1
fi

# Step 6: Collect static files
echo -e "${YELLOW}🎨 Collecting static files...${NC}"
if python manage.py collectstatic --noinput; then
    echo -e "${GREEN}✅ Static files collected.${NC}"
else
    echo -e "${RED}❌ Failed to collect static files.${NC}"
    exit 1
fi


echo -e "${GREEN}🎉 Deployment complete!${NC}"
