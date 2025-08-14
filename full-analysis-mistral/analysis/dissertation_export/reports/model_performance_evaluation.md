# Model Performance Evaluation Report
## Real Dataset Analysis - 2025-08-14 13:10:54

### Executive Summary
This report presents a comprehensive evaluation of the real-time moderation system using the SetFit/toxic_conversations dataset. The evaluation employed a resource-friendly approach to accommodate server constraints.

### Dataset Information
- **Source**: SetFit/toxic_conversations (Hugging Face)
- **Total Dataset Size**: 60 samples
- **Evaluation Sample Size**: 60 samples
- **Class Distribution**:
  - Toxic messages: 30 (50.0%)
  - Non-toxic messages: 30 (50.0%)

### Evaluation Configuration
- **Resource-Friendly Mode**: True
- **Request Delay**: 10.0s
- **Timeout**: 60.0s
- **Max Retries**: 3
- **Success Rate**: 100.0%

### Performance Metrics

#### Classification Performance
- **Accuracy**: 0.7667 (76.7%)
- **Precision**: 0.9444 (94.4%)
- **Recall**: 0.5667 (56.7%)
- **F1-Score**: 0.7083 (70.8%)
- **ROC AUC**: 0.8883

#### Response Time Analysis
- **Mean Response Time**: 3.040 seconds
- **Median Response Time**: 3.021 seconds
- **Standard Deviation**: 0.352 seconds
- **Min Response Time**: 2.285 seconds
- **Max Response Time**: 3.927 seconds

### Confusion Matrix Analysis
The confusion matrix reveals the following classification patterns:
           Non-Toxic  Toxic
Non-Toxic         29      1
Toxic             13     17

### Per-Class Performance Analysis

#### Non-Toxic Class Performance
- **Precision**: 0.6905
- **Recall**: 0.9667
- **F1-Score**: 0.8056
- **Support**: 30.0 samples

#### Toxic Class Performance
- **Precision**: 0.9444
- **Recall**: 0.5667
- **F1-Score**: 0.7083
- **Support**: 30.0 samples

### Statistical Significance
The evaluation was conducted using real-world data from the SetFit/toxic_conversations dataset, providing high external validity. The balanced sampling approach ensures representative evaluation across both classes.

### Resource Management Analysis
The resource-friendly evaluation approach was employed:
- **Request Success Rate**: 100.0%
- **Failed Requests**: 0
- **Total Requests**: 60

### Recommendations

#### Performance Optimization
1. **Accuracy Improvement**: Current accuracy of 76.7% falls below typical production standards (85%+)
2. **Precision-Recall Balance**: Imbalanced precision (0.944) and recall (0.567)
3. **Response Time**: Average response time of 3.04s is acceptable for real-time applications

#### Resource Management
1. **Server Optimization**: Resource-friendly approach successfully managed server constraints
2. **Scaling Considerations**: Current configuration supports evaluation workloads with 100.0% success rate

### Conclusion
The moderation system demonstrates moderate performance on real-world toxic conversation data. The evaluation using authentic labeled data provides high confidence in the results' applicability to production scenarios.

### Technical Details
- **Evaluation Date**: 2025-08-14 13:10:54
- **Dataset Source**: SetFit/toxic_conversations
- **Evaluation Framework**: Custom academic evaluation suite
- **Statistical Methods**: Scikit-learn metrics with balanced sampling
- **Visualization**: Comprehensive performance dashboard generated

---
*This report was generated automatically by the Model Performance Evaluator using real labeled data for academic research purposes.*
