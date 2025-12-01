#!/bin/bash
# Deploy frontend to Breezehost

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Frontend Deployment to Breezehost${NC}"
echo "===================================="

# Check if dist folder exists
if [ ! -d "frontend/dist" ]; then
    echo -e "${RED}❌ frontend/dist folder not found${NC}"
    echo "Run 'npm run build' in the frontend folder first"
    exit 1
fi

echo -e "${GREEN}✓ dist folder found${NC}"

# Configuration
REMOTE_HOST="thenewafricagroup.com"
REMOTE_USER="your_breezehost_user"
REMOTE_PATH="/home/your_username/public_html"  # Adjust based on your Breezehost setup
REMOTE_SSH_KEY="/path/to/your/private/key"      # Your SSH key path

echo "Configuration:"
echo "  Host: $REMOTE_HOST"
echo "  User: $REMOTE_USER"
echo "  Remote Path: $REMOTE_PATH"
echo ""

# Ask for confirmation
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 1
fi

# Deploy
echo -e "${YELLOW}Deploying frontend files...${NC}"

# Use rsync to upload files (preserves permissions, faster for updates)
rsync -avz \
    -e "ssh -i $REMOTE_SSH_KEY" \
    frontend/dist/ \
    "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH" \
    --delete \
    --exclude='.git'

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Deployment successful!${NC}"
    echo ""
    echo "Frontend deployed to: https://$REMOTE_HOST"
    echo ""
    echo "Next steps:"
    echo "1. Clear your browser cache (Ctrl+Shift+Del or Cmd+Shift+Del)"
    echo "2. Test the group update feature"
    echo "3. Verify PUT requests are now routed to POST /update_group/"
else
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi
