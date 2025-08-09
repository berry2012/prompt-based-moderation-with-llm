#!/bin/bash
# Script to run the moderation system analysis

echo "======================================================"
echo "  Real-Time Moderation System - Academic Analysis"
echo "======================================================"
echo ""

# Create necessary directories
echo "Setting up directories..."
mkdir -p data results figures tables
echo "✓ Directories created"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check for required Python packages
echo "Checking Python dependencies..."
python3 -c "
import sys
required = ['pandas', 'numpy', 'matplotlib', 'seaborn', 'sklearn', 'scipy', 'tabulate']
missing = []
for package in required:
    try:
        __import__(package)
    except ImportError:
        missing.append(package)
if missing:
    print(f'Error: Missing Python packages: {\", \".join(missing)}')
    sys.exit(1)
else:
    print('✓ All required Python packages are installed')
"

if [ $? -ne 0 ]; then
    echo ""
    echo "Please install missing packages with:"
    echo "pip install -r requirements.txt"
    exit 1
fi
echo ""

# Check if data file exists
if [ ! -f "experiment-data.csv" ]; then
    echo "Error: Required data file (experiment-data.csv) not found."
    exit 1
fi

# Step 1: Preprocess data
echo "Step 1: Preprocessing data..."
python3 preprocess_data.py
echo "✓ Data preprocessing complete"
echo ""

# Step 2: Run moderation analysis
echo "Step 2: Running moderation system analysis..."
python3 moderation_analysis.py
echo "✓ Moderation analysis complete"
echo ""

# Print summary
echo "======================================================"
echo "  Analysis Complete!"
echo "======================================================"
echo ""
echo "Results available in:"
echo "  - results/performance_metrics.json"
echo "  - results/analysis_report.md"
echo ""
echo "Visualizations saved to:"
echo "  - figures/"
echo ""
echo "Tables saved to:"
echo "  - tables/"
echo ""
echo "To view the report, run:"
echo "  less results/analysis_report.md"
echo ""

exit 0
