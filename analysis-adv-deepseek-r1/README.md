# Moderation System Analysis

This directory contains scripts for analyzing the performance of the LLM used in the real-time moderation system using the experiment-data.csv dataset.

## Prerequisites

Before running the analysis, you need to install the required Python packages:

```bash
cd analysis-adv
python3 -m venv /tmp/.venv
source /tmp/.venv/bin/activate
pip install -r requirements.txt
```

## Running the Analysis

To run the complete analysis pipeline, execute:

```bash
./run_analysis.sh
```

This will:
1. Preprocess the experiment-data.csv file
2. Run the moderation system analysis
3. Generate performance metrics and visualizations
4. Create an analysis report

## Files and Directories

- `experiment-data.csv`: The dataset containing text messages and their true labels
- `preprocess_data.py`: Script to clean and prepare the dataset
- `moderation_analysis.py`: Script to analyze the moderation system performance
- `run_analysis.sh`: Shell script to run the complete analysis pipeline
- `requirements.txt`: List of required Python packages

After running the analysis, the following directories will be created:

- `data/`: Contains the processed dataset and statistics
- `results/`: Contains performance metrics and the analysis report
- `figures/`: Contains visualizations of the results
- `tables/`: Markdown tables ready for inclusion in your dissertation

## Analysis Report

The analysis report is generated at `results/analysis_report.md` and includes:

- Dataset summary
- Performance metrics (accuracy, precision, recall, F1 score)
- Confusion matrix
- Latency analysis
- Visualizations
- Conclusion and recommendations

## Customizing the Analysis

To modify the analysis:

1. Edit `preprocess_data.py` to change how the dataset is processed
2. Edit `moderation_analysis.py` to change the analysis methods or metrics
3. Run `./run_analysis.sh` to execute the updated analysis
