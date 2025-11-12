#!/bin/bash
# Deployment script for SkyScansGames server
# Run this on your server after pushing to GitHub

set -e  # Exit on error

echo "=========================================="
echo "SkyScansGames Deployment Script"
echo "=========================================="
echo ""

# Navigate to project directory
echo "Step 1: Navigating to project directory..."
cd /root/SkyScansGames || { echo "Error: Could not find /root/SkyScansGames"; exit 1; }
echo "✓ Found project directory"
echo ""

# Pull latest changes
echo "Step 2: Pulling latest changes from GitHub..."
git pull origin Develop || { echo "Error: Git pull failed"; exit 1; }
echo "✓ Latest changes pulled"
echo ""

# Build frontend
echo "Step 3: Building frontend..."
cd frontend || { echo "Error: Could not find frontend directory"; exit 1; }
npm run build || { echo "Error: Frontend build failed"; exit 1; }
echo "✓ Frontend built successfully"
echo ""

# Set proper permissions
echo "Step 4: Setting permissions..."
chown -R nginx:nginx /root/SkyScansGames/frontend/build 2>/dev/null || echo "⚠ Warning: Could not set nginx permissions (may need manual fix)"
echo "✓ Permissions set"
echo ""

# Reload nginx
echo "Step 5: Reloading nginx..."
if systemctl reload nginx 2>/dev/null; then
  echo "✓ Nginx reloaded successfully"
elif service nginx reload 2>/dev/null; then
  echo "✓ Nginx reloaded successfully"
else
  echo "⚠ Warning: Could not reload nginx automatically"
  echo "  You may need to run: systemctl reload nginx"
fi
echo ""

echo "=========================================="
echo "Deployment Complete! ✓"
echo "=========================================="
echo ""
echo "Your changes should now be live on the server."
echo "Visit your site to verify the updates."
echo ""
