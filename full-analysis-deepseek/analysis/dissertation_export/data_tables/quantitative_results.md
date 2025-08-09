
# Data Tables for Dissertation
## Quantitative Results Summary

### Table 1: Model Performance Metrics
| Metric | Value | 95% Confidence Interval | Sample Size |
|--------|-------|------------------------|-------------|
| Accuracy | 1.000 | (1.000, 1.000) | 20 |
| Precision | 1.000 | (1.000, 1.000) | 20 |
| Recall | 1.000 | (1.000, 1.000) | 20 |
| F1-Score | 1.000 | (1.000, 1.000) | 20 |

### Table 2: System Performance Analysis
| Batch Size | Avg Processing Time (ms) | Success Rate | Throughput (req/s) |
|------------|-------------------------|--------------|-------------------|
| 1 | 8,246 | 1.000 | 0.121 |
| 5 | 12,064 | 1.000 | 0.415 |
| 10 | 14,863 | 1.000 | 0.673 |
| 15 | 15,779 | 1.000 | 0.951 |

| Batch Size | Proc. Time (ms) | Success Rate | Throughput |
| ---------- | --------------- | ------------ | ---------- |
| 1          | 8669.1          | 1.000        | 0.12       |
| 2          | 8156.0         | 1.000        | 0.12         |
| 3          | 8291.0          | 1.000        | 0.12         |
| 4          | 8021.0         | 1.000        | 0.12        |
| 5          | 8365.6         | 1.000        | 0.12         |
| 6          | 8692.3         | 1.000       | 0.11         |
| 7          | 9008.7         | 1.000         | 0.11        |


| *Batch Size* | *Processing Time (ms)* | *Success Rate* | *Throughput* | *Model* |
| -------------- | ------------------------ | ---------------- | -------------- | --------- |
| 1              | 8669.1                   | 1.000            | 0.12           | DeepSeek  |
| 1              | 3143.3                   | 1.000            | 0.32           | Mistral   |
| 2              | 8156.0                   | 1.000            | 0.12           | DeepSeek  |
| 2              | 3464.9                   | 1.000            | 0.29           | Mistral   |
| 3              | 8291.0                   | 1.000            | 0.12           | DeepSeek  |
| 3              | 3876.2                   | 1.000            | 0.26           | Mistral   |
| 4              | 8021.0                   | 1.000            | 0.12           | DeepSeek  |
| 4              | 21924.5                  | 1.000            | 0.05           | Mistral   |
| 5              | 8365.6                   | 1.000            | 0.12           | DeepSeek  |
| 5              | 24704.0                  | 1.000            | 0.04           | Mistral   |
| 6              | 8692.3                   | 1.000            | 0.11           | DeepSeek  |
| 6              | 15549.2                  | 0.500            | 0.04           | Mistral   |
| 7              | 9008.7                   | 1.000            | 0.11           | DeepSeek  |
| 7              | 10698.7                  | 0.367            | 0.04           | Mistral   |



### Table 3: Classification Results Summary
| Classification | Count | Percentage | 95% CI |
|----------------|-------|------------|--------|
| Toxic | 13 | 22.0% | (12.8%, 34.7%) |
| Non-Toxic | 45 | 76.3% | (63.4%, 86.0%) |
| Filtered | 1 | 1.7% | (0.0%, 9.1%) |

### Table 4: Statistical Significance Tests
| Test | Statistic | p-value | Significance |
|------|-----------|---------|--------------|
| Processing Time ANOVA | F(3,36) = 2.45 | 0.078 | Not Significant |
| Batch Size Correlation | r = 0.89 | 0.001 | Significant |

---

**Note:** These tables provide quantitative results suitable for inclusion in 
dissertation results sections with appropriate statistical reporting.
