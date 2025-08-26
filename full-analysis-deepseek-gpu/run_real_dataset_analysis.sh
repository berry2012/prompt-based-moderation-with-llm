#!/bin/bash

# Real Dataset Analysis Runner for Moderation System
# =================================================
# This script runs only the real dataset analysis scripts with resource-friendly settings

set -e  # Exit on any error (remove this line if you want to continue on errors)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORTS_DIR="$SCRIPT_DIR/reports"

echo -e "${BLUE}🔬 Starting Real Dataset Analysis${NC}"
echo "Analysis Directory: $SCRIPT_DIR"
echo "Reports Directory: $REPORTS_DIR"

# Create necessary directories
echo -e "\n${YELLOW}📁 Creating directories...${NC}"
mkdir -p "$REPORTS_DIR"
mkdir -p "$REPORTS_DIR/figures"
mkdir -p "$REPORTS_DIR/data"
mkdir -p "$REPORTS_DIR/exports"
mkdir -p "$SCRIPT_DIR/logs"

echo -e "${GREEN}✓ Directories created${NC}"

# Check if dataset file exists
if [ ! -f "$SCRIPT_DIR/dissertation-experiment-data.csv" ]; then
    echo -e "${RED}❌ Dataset file not found: dissertation-experiment-data.csv${NC}"
    echo -e "${YELLOW}Please ensure the SetFit/toxic_conversations dataset is saved as dissertation-experiment-data.csv${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Dataset file found${NC}"

# Change to analysis directory
cd "$SCRIPT_DIR"

# Define real dataset scripts to run in order
declare -a SCRIPTS=(
    "model_evaluation_real.py:Model Evaluation (Real Dataset)"
    "experimental_design_real.py:Experimental Design (Real Dataset)"
    "statistical_analysis.py:Statistical Analysis"
    "run_academic_analysis.py:Academic Analysis"
    "export_for_dissertation.py:Export for Dissertation"
    "view_results.py:View Results"
)

# Function to run a script
run_script() {
    local script_file="$1"
    local script_name="$2"
    
    if [ ! -f "$script_file" ]; then
        echo -e "${YELLOW}⏭️  Skipping $script_name: File not found${NC}"
        return 0
    fi
    
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}Running: $script_name${NC}"
    echo -e "${BLUE}File: $script_file${NC}"
    echo -e "${BLUE}============================================================${NC}"
    
    start_time=$(date +%s)
    
    if python "$script_file"; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        echo -e "${GREEN}✅ $script_name completed successfully (${duration}s)${NC}"
        return 0
    else
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        echo -e "${RED}❌ $script_name failed (${duration}s)${NC}"
        return 1
    fi
}

# Run all scripts
echo -e "\n${YELLOW}🏃 Running real dataset analysis scripts...${NC}"

success_count=0
total_count=0

for script_info in "${SCRIPTS[@]}"; do
    IFS=':' read -r script_file script_name <<< "$script_info"
    total_count=$((total_count + 1))
    
    echo -e "\n${YELLOW}[$total_count/${#SCRIPTS[@]}] Processing: $script_name${NC}"
    
    if run_script "$script_file" "$script_name"; then
        success_count=$((success_count + 1))
    else
        echo -e "${RED}Script failed. Check the error messages above.${NC}"
        # Uncomment the next line if you want to stop on first error
        # exit 1
    fi
done

# Summary
echo -e "\n${BLUE}📊 Real Dataset Analysis Summary${NC}"
echo -e "${GREEN}✅ $success_count/$total_count scripts completed successfully${NC}"
echo -e "${BLUE}📁 Reports saved in: $REPORTS_DIR${NC}"

if [ $success_count -eq $total_count ]; then
    echo -e "\n${GREEN}🎉 All real dataset analysis scripts completed successfully!${NC}"
    echo -e "\n${BLUE}📊 Generated Files:${NC}"
    echo -e "   • model_evaluation_real.png - Real dataset evaluation visualization"
    echo -e "   • model_evaluation_real_report.md - Comprehensive evaluation report"
    echo -e "   • experiment_Real_Dataset_Performance_real.png - Performance experiment results"
    echo -e "\n${YELLOW}💡 Key Benefits of Real Dataset Analysis:${NC}"
    echo -e "   • Uses authentic SetFit/toxic_conversations data"
    echo -e "   • Resource-friendly approach for constrained servers"
    echo -e "   • Balanced sampling for statistical validity"
    echo -e "   • Comprehensive performance metrics"
    echo -e "   • Academic-quality reporting"
    exit 0
else
    echo -e "\n${YELLOW}⚠️  Some scripts failed. Check the output above for details.${NC}"
    exit 1
fi
