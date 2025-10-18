#!/bin/bash

# =============================
# Django Deployment Script for PythonAnywhere
# Author: OA Wisdom Digital Firm
# =============================

# Define project and environment paths
PROJECT_DIR=~/NAG
VENV_DIR=$PROJECT_DIR/.venv
WEBAPP_NAME="newafricagroup.pythonanywhere.com"

# Add colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting automated deployment for $WEBAPP_NAME...${NC}"

# Step 1: Navigate to project directory
cd "$PROJECT_DIR" || { echo -e "${RED}❌ Project directory not found!${NC}"; exit 1; }

# Step 2: Clean and pull the latest code
echo -e "${YELLOW}📦 Pulling latest code from GitHub...${NC}"
git reset --hard HEAD
git clean -fd
if git pull origin main; then
    echo -e "${GREEN}✅ Code updated successfully.${NC}"
else
    echo -e "${RED}❌ Git pull failed!${NC}"
    exit 1
fi

# Step 3: Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}🧠 Activating virtual environment...${NC}"
    source "$VENV_DIR/bin/activate"
else
    echo -e "${RED}❌ Virtual environment not found at $VENV_DIR${NC}"
    exit 1
fi

# Step 4: Make and apply database migrations
echo -e "${YELLOW}🛠️  Creating new migrations if needed...${NC}"
if python manage.py makemigrations; then
    echo -e "${GREEN}✅ Makemigrations complete.${NC}"
else
    echo -e "${RED}❌ Makemigrations failed!${NC}"
    exit 1
fi

echo -e "${YELLOW}🗃️  Applying migrations...${NC}"
if python manage.py migrate --noinput; then
    echo -e "${GREEN}✅ Migrations applied successfully.${NC}"
else
    echo -e "${RED}❌ Migration failed!${NC}"
    exit 1
fi

# Step 5: Collect static files
echo -e "${YELLOW}🎨 Collecting static files...${NC}"
if python manage.py collectstatic --noinput; then
    echo -e "${GREEN}✅ Static files collected.${NC}"
else
    echo -e "${RED}❌ Failed to collect static files.${NC}"
    exit 1
fi

# Step 6: Reload the PythonAnywhere web app
echo -e "${YELLOW}🔄 Reloading web app...${NC}"
if "$VENV_DIR/bin/pa_reload_webapp" "$WEBAPP_NAME"; then
    echo -e "${GREEN}✅ Web app reloaded successfully.${NC}"
else
    echo -e "${RED}⚠️  Could not reload automatically. Please reload manually from the PythonAnywhere dashboard.${NC}"
fi

echo -e "${GREEN}🎉 Deployment complete!${NC}"
