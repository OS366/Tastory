#!/bin/bash

# Move large data files to a data folder

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}📦 Moving Large Data Files${NC}"
echo "=========================="

# Create data folder
echo -e "${YELLOW}Creating data folder...${NC}"
mkdir -p data

# Move CSV and parquet files
echo -e "${YELLOW}Moving data files...${NC}"
for file in *.csv *.parquet upload_progress.pkl; do
    if [ -f "$file" ]; then
        mv "$file" data/
        echo "  Moved $file to data/"
    fi
done

# Update .gitignore to exclude data folder
echo -e "\n${YELLOW}Updating .gitignore...${NC}"
if ! grep -q "^data/$" .gitignore; then
    echo -e "\n# Large data files\ndata/" >> .gitignore
    echo "  Added data/ to .gitignore"
fi

echo -e "\n${GREEN}✅ Data files moved successfully!${NC}"
echo -e "\nNote: The data folder contains the original CSV/parquet files used to populate MongoDB."
echo "These files are not needed for running the application but are kept for reference."
echo "Total size saved from repository: ~3.5GB" 