# Moderation System Analysis Report

## Dataset Summary

The analysis was conducted using a dataset of 60 messages, with the following distribution:

| Category   |   Count | Percentage   |
|:-----------|--------:|:-------------|
| Toxic      |      30 | 50.0%        |
| Non-Toxic  |      30 | 50.0%        |
| Total      |      60 | 100.0%       |

## Performance Metrics

The moderation system achieved the following performance metrics:

| Metric    |   Value | 95% Confidence Interval   |
|:----------|--------:|:--------------------------|
| Accuracy  |  0.7667 | [0.6500, 0.8671]          |
| Precision |  0.9444 | N/A                       |
| Recall    |  0.5667 | N/A                       |
| F1 Score  |  0.7083 | N/A                       |
| ROC AUC   |  0.8867 | N/A                       |
| PR AUC    |  0.8966 | N/A                       |

## Classification Report

Detailed classification metrics by class:

| Class         | Precision   | Recall   |   F1-Score |   Support |
|:--------------|:------------|:---------|-----------:|----------:|
| Non-Toxic (0) | 0.6905      | 0.9667   |     0.8056 |        30 |
| Toxic (1)     | 0.9444      | 0.5667   |     0.7083 |        30 |
| Accuracy      |             |          |     0.7667 |        60 |
| Macro Avg     | 0.8175      | 0.7667   |     0.7569 |        60 |
| Weighted Avg  | 0.8175      | 0.7667   |     0.7569 |        60 |

## Confusion Matrix

The confusion matrix shows the distribution of predictions versus actual labels:

|                  |   Predicted Non-Toxic |   Predicted Toxic |
|:-----------------|----------------------:|------------------:|
| Actual Non-Toxic |                    29 |                 1 |
| Actual Toxic     |                    13 |                17 |

## Latency Analysis

The system demonstrated the following latency characteristics:

| Latency Metric     |   Value (seconds) |
|:-------------------|------------------:|
| Average            |            3.0752 |
| Median             |            3.0638 |
| Standard Deviation |            0.3671 |
| Minimum            |            2.4397 |
| Maximum            |            4.1234 |

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

- **Accuracy**: The moderation system achieved 76.7% accuracy (95% CI: [65.0%, 86.7%]) on the test dataset.
- **Precision**: The system shows a 94.4% precision rate for toxic content detection.
- **Recall**: The recall rate of 56.7% indicates the system's ability to identify toxic content.
- **F1 Score**: The F1 score of 0.7083 represents the harmonic mean of precision and recall.
- **ROC AUC**: The area under the ROC curve of 0.8867 demonstrates the system's ability to discriminate between classes.
- **PR AUC**: The area under the Precision-Recall curve of 0.8966 shows the trade-off between precision and recall.

## Conclusion

This analysis demonstrates the effectiveness of the real-time moderation system in identifying toxic content in chat messages. The system shows 76.7% accuracy with the experiment dataset of toxic and non-toxic messages.

The latency analysis indicates an average processing time of 3.08 seconds per message, which is suitable for real-time applications. Further optimization could focus on reducing the standard deviation of 0.37 seconds to provide more consistent response times.

Areas for improvement include reducing false positives (1 instances) and false negatives (13 instances) to enhance the overall reliability of the moderation system.
