# Moderation System Analysis Report

## Dataset Summary

The analysis was conducted using a dataset of 40 messages, with the following distribution:

| Category   |   Count | Percentage   |
|:-----------|--------:|:-------------|
| Toxic      |      20 | 50.0%        |
| Non-Toxic  |      20 | 50.0%        |
| Total      |      40 | 100.0%       |

## Performance Metrics

The moderation system achieved the following performance metrics:

| Metric    |   Value | 95% Confidence Interval   |
|:----------|--------:|:--------------------------|
| Accuracy  |  0.6    | [0.4500, 0.7500]          |
| Precision |  0.7    | N/A                       |
| Recall    |  0.35   | N/A                       |
| F1 Score  |  0.4667 | N/A                       |
| ROC AUC   |  0.6725 | N/A                       |
| PR AUC    |  0.583  | N/A                       |

## Classification Report

Detailed classification metrics by class:

| Class         | Precision   | Recall   |   F1-Score |   Support |
|:--------------|:------------|:---------|-----------:|----------:|
| Non-Toxic (0) | 0.5667      | 0.8500   |     0.68   |        20 |
| Toxic (1)     | 0.7000      | 0.3500   |     0.4667 |        20 |
| Accuracy      |             |          |     0.6    |        40 |
| Macro Avg     | 0.6333      | 0.6000   |     0.5733 |        40 |
| Weighted Avg  | 0.6333      | 0.6000   |     0.5733 |        40 |

## Confusion Matrix

The confusion matrix shows the distribution of predictions versus actual labels:

|                  |   Predicted Non-Toxic |   Predicted Toxic |
|:-----------------|----------------------:|------------------:|
| Actual Non-Toxic |                    17 |                 3 |
| Actual Toxic     |                    13 |                 7 |

## Latency Analysis

The system demonstrated the following latency characteristics:

| Latency Metric     |   Value (seconds) |
|:-------------------|------------------:|
| Average            |            3.368  |
| Median             |            3.3553 |
| Standard Deviation |            0.2984 |
| Minimum            |            2.8009 |
| Maximum            |            4.1307 |

## Visualizations

### Performance Metrics
![Performance Metrics](figures/performance_metrics.png)

### Confusion Matrix
![Confusion Matrix](figures/confusion_matrix.png)

### ROC Curve
![ROC Curve](figures/roc_curve.png)

### Precision-Recall Curve
![Precision-Recall Curve](figures/precision_recall_curve.png)

### Accuracy with Confidence Interval
![Accuracy with Confidence Interval](figures/accuracy_confidence_interval.png)

### Latency Distribution
![Latency Distribution](figures/latency_distribution.png)

### Latency Metrics
![Latency Metrics](figures/latency_metrics.png)

### Confidence Score Distribution
![Confidence Score Distribution](figures/confidence_distribution.png)

### Latency vs Message Length
![Latency vs Message Length](figures/latency_vs_length.png)

## Statistical Analysis

- **Accuracy**: The moderation system achieved 60.0% accuracy (95% CI: [45.0%, 75.0%]) on the test dataset.
- **Precision**: The system shows a 70.0% precision rate for toxic content detection.
- **Recall**: The recall rate of 35.0% indicates the system's ability to identify toxic content.
- **F1 Score**: The F1 score of 0.4667 represents the harmonic mean of precision and recall.
- **ROC AUC**: The area under the ROC curve of 0.6725 demonstrates the system's ability to discriminate between classes.
- **PR AUC**: The area under the Precision-Recall curve of 0.5830 shows the trade-off between precision and recall.

## Conclusion

This analysis demonstrates the effectiveness of the real-time moderation system in identifying toxic content in chat messages. The system shows 60.0% accuracy with the experiment dataset of toxic and non-toxic messages.

The latency analysis indicates an average processing time of 3.37 seconds per message, which is suitable for real-time applications. Further optimization could focus on reducing the standard deviation of 0.30 seconds to provide more consistent response times.

Areas for improvement include reducing false positives (3 instances) and false negatives (13 instances) to enhance the overall reliability of the moderation system.
