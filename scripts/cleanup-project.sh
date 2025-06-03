#!/bin/bash

# Tastory Project Cleanup Script
# Removes unnecessary files and organizes the codebase

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧹 Tastory Project Cleanup${NC}"
echo "=========================="

# Create a data-scripts folder for database setup scripts
echo -e "${YELLOW}Creating data-scripts folder for database setup files...${NC}"
mkdir -p data-scripts

# Move data processing scripts to data-scripts folder
echo -e "${YELLOW}Moving data processing scripts...${NC}"
for script in clean_recipes.py clean_reviews.py upload_to_mongodb.py generate_embeddings.py create_indexes.py; do
    if [ -f "$script" ]; then
        mv "$script" data-scripts/
        echo "  Moved $script to data-scripts/"
    fi
done

# Remove unnecessary files
echo -e "\n${YELLOW}Removing unnecessary files...${NC}"

# Remove .DS_Store files (macOS)
find . -name ".DS_Store" -type f -delete 2>/dev/null || true
echo "  Removed .DS_Store files"

# Remove __pycache__ directories
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
echo "  Removed __pycache__ directories"

# Remove .pyc files
find . -name "*.pyc" -type f -delete 2>/dev/null || true
echo "  Removed .pyc files"

# Remove log files from frontend
if [ -f "frontend/firebase-debug.log" ]; then
    rm frontend/firebase-debug.log
    echo "  Removed frontend/firebase-debug.log"
fi

# Remove app_minimal.py (no longer needed)
if [ -f "app_minimal.py" ]; then
    rm app_minimal.py
    echo "  Removed app_minimal.py"
fi

# Remove root package.json and package-lock.json (Tailwind dependencies not used)
echo -e "\n${YELLOW}Removing unused root package files...${NC}"
if [ -f "package.json" ]; then
    # Check if it only contains unused dependencies
    if grep -q "tailwindcss" package.json; then
        rm package.json package-lock.json 2>/dev/null || true
        echo "  Removed unused root package.json and package-lock.json (Tailwind not used)"
        
        # Remove node_modules from root if it exists
        if [ -d "node_modules" ]; then
            rm -rf node_modules
            echo "  Removed root node_modules directory"
        fi
    fi
fi

# Update .gitignore to exclude these files
echo -e "\n${YELLOW}Updating .gitignore...${NC}"
cat >> .gitignore << 'EOL'

# macOS
.DS_Store

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Logs
*.log
firebase-debug.log

# Temporary files
*.tmp
*.temp
*.bak
*~

# IDE
.vscode/
.idea/
*.swp
*.swo
EOL

echo "  Updated .gitignore"

# Show summary
echo -e "\n${GREEN}✅ Cleanup complete!${NC}"
echo -e "\nProject structure:"
echo "  - Data processing scripts moved to: data-scripts/"
echo "  - Removed unnecessary files (.DS_Store, logs, cache)"
echo "  - Removed unused Tailwind dependencies from root"
echo "  - Updated .gitignore to prevent these files from being committed"

echo -e "\n${YELLOW}Note:${NC} The data-scripts folder contains database setup scripts."
echo "Keep them if you might need to recreate the database in the future." 