#!/bin/bash

# Analysis Environment Setup Script
# =================================
# This script sets up the analysis environment with all required dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🔧 Setting up Analysis Environment${NC}"
echo "Directory: $SCRIPT_DIR"

# Change to analysis directory
cd "$SCRIPT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "\n${YELLOW}🐍 Creating Python virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "\n${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}🔌 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "\n${YELLOW}📦 Upgrading pip...${NC}"
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo -e "\n${YELLOW}📚 Installing requirements...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Requirements installed${NC}"
else
    echo -e "\n${YELLOW}📚 Installing common analysis packages...${NC}"
    pip install matplotlib pandas numpy seaborn scipy scikit-learn jupyter
    echo -e "${GREEN}✓ Common packages installed${NC}"
fi

# Create directory structure
echo -e "\n${YELLOW}📁 Creating directory structure...${NC}"
mkdir -p reports/figures
mkdir -p reports/data
mkdir -p reports/exports
mkdir -p logs
echo -e "${GREEN}✓ Directories created${NC}"

# Check if data files exist
echo -e "\n${YELLOW}🔍 Checking for data files...${NC}"
if [ -f "toxic.csv" ] && [ -f "non-toxic.csv" ]; then
    echo -e "${GREEN}✓ Data files found${NC}"
else
    echo -e "${YELLOW}⚠️  Data files (toxic.csv, non-toxic.csv) not found${NC}"
    echo -e "${YELLOW}   Make sure to have your data files in the analysis directory${NC}"
fi

echo -e "\n${GREEN}🎉 Setup complete!${NC}"
echo -e "\n${BLUE}Next steps:${NC}"
echo -e "1. Activate the virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "2. Run all analysis: ${YELLOW}./run_analysis.sh${NC}"
echo -e "   Or use Python version: ${YELLOW}python run_all_analysis.py${NC}"
echo -e "3. Check results in: ${YELLOW}reports/${NC}"

echo -e "\n${BLUE}Available commands:${NC}"
echo -e "• ${YELLOW}./setup_analysis.sh${NC} - Setup environment (this script)"
echo -e "• ${YELLOW}./run_analysis.sh${NC} - Run all analysis scripts (bash version)"
echo -e "• ${YELLOW}python run_all_analysis.py${NC} - Run all analysis scripts (Python version)"
echo -e "• ${YELLOW}python run_all_analysis.py --verbose${NC} - Run with detailed output"
echo -e "• ${YELLOW}python run_all_analysis.py --skip-errors${NC} - Continue on errors"
