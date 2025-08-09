# Real Dataset Analysis for Moderation System - END-TO-END SIMULATIONS

This directory contains enhanced analysis scripts that use real labeled data from the SetFit/toxic_conversations dataset instead of hardcoded or randomly generated data. The scripts implement resource-friendly approaches suitable for constrained server environments.

## 🎯 Key Improvements

### ✅ Real Data Integration
- **Authentic Dataset**: Uses SetFit/toxic_conversations from Hugging Face
- **Balanced Sampling**: Ensures statistical validity with balanced class representation
- **Stratified Sampling**: Maintains original class distributions when needed
- **Ground Truth Labels**: Real human-annotated toxic/non-toxic classifications

### ✅ Resource-Friendly Approach
- **Configurable Delays**: Adjustable request delays (2-3s) for constrained servers
- **Extended Timeouts**: Longer timeouts (45-60s) to handle slow responses
- **Retry Logic**: Robust retry mechanisms with exponential backoff
- **Batch Management**: Intelligent batching with delays between batches
- **Error Handling**: Graceful handling of timeouts and connection errors

### ✅ Academic Quality
- **Statistical Rigor**: Proper sampling methods and confidence intervals
- **Comprehensive Metrics**: Accuracy, precision, recall, F1-score, ROC AUC
- **Detailed Reporting**: Academic-quality reports with methodology sections
- **Reproducible Results**: Fixed random seeds for consistent results

## 📁 New Files

### Core Scripts
- **`dataset_loader.py`** - Loads and processes the SetFit/toxic_conversations dataset
- **`model_evaluation_real.py`** - Model evaluation using real labeled data
- **`experimental_design_real.py`** - Performance experiments with real data
- **`run_real_dataset_analysis.sh`** - Script to run only real dataset analysis

### Required Data
- **`dissertation-experiment-data.csv`** - SetFit/toxic_conversations dataset in CSV format

## 🚀 Quick Start

### 1. Prepare Dataset
Ensure you have the SetFit/toxic_conversations dataset saved as `dissertation-experiment-data.csv` with columns:
- `text`: The message text
- `true_label`: Binary label (0=non-toxic, 1=toxic)

### 2. Run Real Dataset Analysis

```bash
cd full-analysis-deepseek
python3 -m venv /tmp/.venv
source /tmp/.venv/bin/activate
pip install -r requirements.txt

```

Then..

```bash
# Run only the real dataset scripts (recommended)
./run_real_dataset_analysis.sh

# Or run all scripts including real dataset versions
./run_analysis.sh
```

### 3. Individual Script Usage
```bash
# Test dataset loader
python dataset_loader.py

# Run model evaluation with real data
python model_evaluation_real.py

# Run performance experiments with real data
python experimental_design_real.py
```

## ⚙️ Configuration Options

### Resource-Friendly Mode (Default)
```python
# Optimized for constrained servers
evaluator = ModelPerformanceEvaluator(resource_friendly=True)
# - Request delay: 2.0s
# - Timeout: 45.0s
# - Max retries: 5
# - Batch delay: 5.0s
```

### Standard Mode
```python
# For high-performance servers
evaluator = ModelPerformanceEvaluator(resource_friendly=False)
# - Request delay: 0.5s
# - Timeout: 30.0s
# - Max retries: 3
# - Batch delay: 1.0s
```

## 📊 Generated Outputs

### Model Evaluation
- **`model_evaluation_real.png`** - Comprehensive performance visualization
- **`model_evaluation_real_report.md`** - Detailed academic report
- Metrics: Accuracy, Precision, Recall, F1-Score, ROC AUC
- Analysis: Confusion matrix, response times, class distribution

### Experimental Design
- **`experiment_Real_Dataset_Performance_real.png`** - Performance experiment results
- Analysis: Batch processing times, success rates, throughput
- Resource efficiency metrics and optimization recommendations

## 🔬 Dataset Statistics

Based on your `dissertation-experiment-data.csv`:
- **Total Samples**: 60 messages
- **Class Distribution**: 50% toxic, 50% non-toxic (balanced)
- **Text Length**: Mean 306 characters, range 6-999 characters
- **Source**: SetFit/toxic_conversations (Hugging Face)

## 📈 Key Benefits

### 1. **Real-World Validity**
- Uses authentic human-annotated data
- Reflects actual toxic conversation patterns
- Higher external validity than synthetic data

### 2. **Resource Management**
- Handles server timeouts gracefully
- Implements intelligent retry logic
- Manages request rates for constrained environments

### 3. **Statistical Rigor**
- Balanced sampling for unbiased evaluation
- Proper confidence intervals and significance testing
- Reproducible results with fixed random seeds

### 4. **Academic Quality**
- Comprehensive methodology documentation
- Publication-ready visualizations and reports
- Follows academic standards for experimental design

## 🛠️ Troubleshooting

### Common Issues

#### Dataset Not Found
```bash
❌ Dataset file not found: dissertation-experiment-data.csv
```
**Solution**: Ensure the SetFit/toxic_conversations dataset is saved as `dissertation-experiment-data.csv` in the analysis directory.

#### Server Timeouts
```bash
⏰ Request timeout, retrying in 6.0s...
```
**Solution**: The resource-friendly mode automatically handles this with retries and longer delays.

#### Connection Errors
```bash
🔌 Connection error, retrying in 4.0s...
```
**Solution**: Ensure the moderation system is running on `localhost:8000` and accessible.

### Performance Optimization

#### For Faster Evaluation
```python
# Use smaller sample sizes
evaluator.collect_evaluation_data(sample_size=20)

# Use standard mode if server can handle it
evaluator = ModelPerformanceEvaluator(resource_friendly=False)
```

#### For Better Reliability
```python
# Increase delays and retries
evaluator.request_delay = 3.0
evaluator.max_retries = 7
evaluator.timeout = 60.0
```

## 📚 Academic Usage

### For Dissertation
1. **Methodology Section**: Reference the balanced sampling approach and resource-friendly evaluation strategy
2. **Results Section**: Use the comprehensive metrics and statistical analysis
3. **Figures**: Include the generated visualizations (publication-ready)
4. **Validation**: Emphasize the use of real human-annotated data for external validity

### For Publications
- The evaluation methodology follows academic standards
- Results include proper statistical measures and confidence intervals
- Reproducible with documented random seeds and parameters
- Comprehensive error analysis and resource management documentation

## 🔄 Integration with Existing Analysis

The real dataset scripts are designed to complement, not replace, the existing analysis:

- **Original scripts**: Continue to work with hardcoded/generated data
- **Real dataset scripts**: Provide enhanced analysis with authentic data
- **Combined analysis**: Run both for comprehensive evaluation
- **Flexible configuration**: Choose resource-friendly or standard modes as needed

## 🎯 Next Steps

1. **Expand Dataset**: Consider using larger samples from the full SetFit/toxic_conversations dataset
2. **Cross-Validation**: Implement k-fold cross-validation for more robust evaluation
3. **Comparative Analysis**: Compare results between synthetic and real data
4. **Performance Tuning**: Optimize resource-friendly parameters based on your server capabilities
5. **Extended Metrics**: Add domain-specific metrics relevant to your research focus

---

*This enhanced analysis framework provides the foundation for rigorous academic evaluation of moderation systems using real-world data while accommodating resource constraints.*
