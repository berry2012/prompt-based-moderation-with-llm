#!/usr/bin/env python3
"""
Advanced Statistical Analysis for Moderation System

This script performs detailed statistical analysis on the moderation results,
including hypothesis testing, confidence intervals, and correlation analysis.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.metrics import roc_curve, auc, precision_recall_curve
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("statistical_analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create output directories
os.makedirs('results/stats', exist_ok=True)
os.makedirs('figures/stats', exist_ok=True)

class StatisticalAnalysis:
    def __init__(self, results_path='results/moderation_results.json'):
        """Initialize with path to moderation results."""
        self.results_path = results_path
        self.load_data()
        
    def load_data(self):
        """Load moderation results data."""
        try:
            with open(self.results_path, 'r') as f:
                self.results = json.load(f)
                
            # Convert to DataFrame for easier analysis
            self.df = pd.DataFrame(self.results)
            
            # Add binary columns
            self.df['ground_truth_binary'] = self.df['ground_truth'].apply(lambda x: 1 if x == 'toxic' else 0)
            self.df['prediction_binary'] = self.df['prediction'].apply(lambda x: 1 if x == 'toxic' else 0)
            
            # Filter out errors
            self.df_valid = self.df[self.df['prediction'] != 'error']
            
            logger.info(f"Loaded {len(self.df)} results, {len(self.df_valid)} valid results")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def confidence_intervals(self):
        """Calculate confidence intervals for key metrics."""
        logger.info("Calculating confidence intervals")
        
        # Function to calculate bootstrap confidence intervals
        def bootstrap_ci(data, func, n_bootstrap=1000, ci=0.95):
            bootstrap_results = []
            for _ in range(n_bootstrap):
                sample = np.random.choice(data, size=len(data), replace=True)
                bootstrap_results.append(func(sample))
            
            lower_percentile = (1 - ci) / 2 * 100
            upper_percentile = (1 + ci) / 2 * 100
            return np.percentile(bootstrap_results, [lower_percentile, upper_percentile])
        
        # Calculate confidence intervals for accuracy
        y_true = self.df_valid['ground_truth_binary'].values
        y_pred = self.df_valid['prediction_binary'].values
        
        # Accuracy function
        def accuracy(y_true, y_pred):
            return np.mean(y_true == y_pred)
        
        # Calculate observed accuracy
        observed_accuracy = accuracy(y_true, y_pred)
        
        # Calculate bootstrap samples for accuracy
        bootstrap_samples = []
        for _ in range(1000):
            # Sample with replacement
            indices = np.random.choice(len(y_true), size=len(y_true), replace=True)
            bootstrap_samples.append(accuracy(y_true[indices], y_pred[indices]))
        
        # Calculate 95% confidence interval
        ci_lower = np.percentile(bootstrap_samples, 2.5)
        ci_upper = np.percentile(bootstrap_samples, 97.5)
        
        # Store results
        accuracy_ci = {
            "metric": "accuracy",
            "observed": observed_accuracy,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "ci_width": ci_upper - ci_lower
        }
        
        # Calculate confidence intervals for latency
        latencies = self.df_valid['latency'].values
        mean_latency = np.mean(latencies)
        
        # Standard error of the mean
        sem = stats.sem(latencies)
        
        # 95% confidence interval
        ci_lower_latency, ci_upper_latency = stats.t.interval(0.95, len(latencies)-1, loc=mean_latency, scale=sem)
        
        latency_ci = {
            "metric": "latency",
            "observed": mean_latency,
            "ci_lower": ci_lower_latency,
            "ci_upper": ci_upper_latency,
            "ci_width": ci_upper_latency - ci_lower_latency
        }
        
        # Store all confidence intervals
        confidence_intervals = {
            "accuracy": accuracy_ci,
            "latency": latency_ci
        }
        
        # Save results
        with open('results/stats/confidence_intervals.json', 'w') as f:
            json.dump(confidence_intervals, f, indent=2)
            
        # Visualize confidence intervals
        plt.figure(figsize=(10, 6))
        
        metrics = ['Accuracy', 'Latency (normalized)']
        observed = [accuracy_ci['observed'], latency_ci['observed'] / max(latencies)]
        lower = [accuracy_ci['ci_lower'], latency_ci['ci_lower'] / max(latencies)]
        upper = [accuracy_ci['ci_upper'], latency_ci['ci_upper'] / max(latencies)]
        
        # Calculate error bars
        yerr_lower = [observed[i] - lower[i] for i in range(len(observed))]
        yerr_upper = [upper[i] - observed[i] for i in range(len(observed))]
        
        plt.errorbar(metrics, observed, yerr=[yerr_lower, yerr_upper], fmt='o', capsize=10, 
                    color='blue', ecolor='black', markersize=8)
        
        for i, v in enumerate(observed):
            if i == 0:  # Accuracy
                plt.text(i, v + 0.02, f"{v:.3f}", ha='center')
            else:  # Latency
                plt.text(i, v + 0.02, f"{latency_ci['observed']:.2f}s", ha='center')
        
        plt.ylim(0, 1.1)
        plt.title('95% Confidence Intervals for Key Metrics')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig('figures/stats/confidence_intervals.png', dpi=300)
        
        return confidence_intervals
    
    def hypothesis_testing(self):
        """Perform hypothesis testing on key metrics."""
        logger.info("Performing hypothesis testing")
        
        # 1. Test if accuracy is better than random chance (0.5)
        y_true = self.df_valid['ground_truth_binary'].values
        y_pred = self.df_valid['prediction_binary'].values
        
        # Calculate accuracy
        accuracy = np.mean(y_true == y_pred)
        
        # Binomial test (is accuracy significantly better than 0.5?)
        n_correct = np.sum(y_true == y_pred)
        n_total = len(y_true)
        binom_result = stats.binom_test(n_correct, n_total, p=0.5, alternative='greater')
        
        # 2. Test if latency is correlated with message length
        message_lengths = self.df_valid['message'].apply(len).values
        latencies = self.df_valid['latency'].values
        
        # Pearson correlation
        pearson_r, pearson_p = stats.pearsonr(message_lengths, latencies)
        
        # Spearman rank correlation
        spearman_r, spearman_p = stats.spearmanr(message_lengths, latencies)
        
        # 3. Test if confidence scores are different between correct and incorrect predictions
        correct_predictions = self.df_valid['ground_truth_binary'] == self.df_valid['prediction_binary']
        
        confidence_correct = self.df_valid.loc[correct_predictions, 'confidence'].values
        confidence_incorrect = self.df_valid.loc[~correct_predictions, 'confidence'].values
        
        # t-test for confidence scores
        if len(confidence_incorrect) > 0:
            ttest_result = stats.ttest_ind(confidence_correct, confidence_incorrect, equal_var=False)
            ttest_pvalue = ttest_result.pvalue
        else:
            ttest_pvalue = None
        
        # Store results
        hypothesis_tests = {
            "accuracy_vs_random": {
                "test": "binomial",
                "null_hypothesis": "Accuracy is not better than random chance (0.5)",
                "alternative": "Accuracy is better than random chance",
                "p_value": binom_result,
                "significant": binom_result < 0.05,
                "interpretation": "Accuracy is significantly better than random chance" if binom_result < 0.05 else "Accuracy is not significantly better than random chance"
            },
            "latency_vs_length": {
                "test": "correlation",
                "pearson_r": pearson_r,
                "pearson_p": pearson_p,
                "spearman_r": spearman_r,
                "spearman_p": spearman_p,
                "significant": pearson_p < 0.05,
                "interpretation": "Latency is significantly correlated with message length" if pearson_p < 0.05 else "Latency is not significantly correlated with message length"
            },
            "confidence_correct_vs_incorrect": {
                "test": "t-test",
                "p_value": ttest_pvalue,
                "significant": ttest_pvalue < 0.05 if ttest_pvalue is not None else None,
                "interpretation": "Confidence scores are significantly different between correct and incorrect predictions" if ttest_pvalue is not None and ttest_pvalue < 0.05 else "Confidence scores are not significantly different between correct and incorrect predictions" if ttest_pvalue is not None else "Not enough incorrect predictions to perform test"
            }
        }
        
        # Save results
        with open('results/stats/hypothesis_tests.json', 'w') as f:
            json.dump(hypothesis_tests, f, indent=2)
            
        # Visualize correlation between message length and latency
        plt.figure(figsize=(10, 6))
        
        plt.scatter(message_lengths, latencies, alpha=0.6, color='blue')
        
        # Add trend line
        z = np.polyfit(message_lengths, latencies, 1)
        p = np.poly1d(z)
        plt.plot(message_lengths, p(message_lengths), "r--", alpha=0.8)
        
        plt.xlabel('Message Length (characters)')
        plt.ylabel('Latency (seconds)')
        plt.title(f'Latency vs Message Length\nPearson r={pearson_r:.3f}, p={pearson_p:.4f}')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('figures/stats/latency_correlation.png', dpi=300)
        
        # Visualize confidence scores for correct vs incorrect predictions
        if len(confidence_incorrect) > 0:
            plt.figure(figsize=(10, 6))
            
            data = [confidence_correct, confidence_incorrect]
            labels = ['Correct Predictions', 'Incorrect Predictions']
            
            plt.boxplot(data, labels=labels, patch_artist=True,
                      boxprops=dict(facecolor='lightblue'),
                      medianprops=dict(color='red'))
            
            plt.ylabel('Confidence Score')
            plt.title(f'Confidence Scores: Correct vs Incorrect Predictions\nt-test p-value={ttest_pvalue:.4f}')
            plt.grid(True, axis='y', alpha=0.3)
            plt.tight_layout()
            plt.savefig('figures/stats/confidence_comparison.png', dpi=300)
        
        return hypothesis_tests
    
    def roc_analysis(self):
        """Perform ROC curve analysis."""
        logger.info("Performing ROC analysis")
        
        # Extract ground truth and confidence scores
        y_true = self.df_valid['ground_truth_binary'].values
        y_scores = self.df_valid['confidence'].values
        
        # For toxic predictions, use confidence directly
        # For non-toxic predictions, use 1 - confidence
        for i, pred in enumerate(self.df_valid['prediction']):
            if pred == 'non_toxic':
                y_scores[i] = 1 - y_scores[i]
        
        # Calculate ROC curve
        fpr, tpr, thresholds = roc_curve(y_true, y_scores)
        roc_auc = auc(fpr, tpr)
        
        # Calculate precision-recall curve
        precision, recall, pr_thresholds = precision_recall_curve(y_true, y_scores)
        pr_auc = auc(recall, precision)
        
        # Store results
        roc_results = {
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "fpr": fpr.tolist(),
            "tpr": tpr.tolist(),
            "thresholds": thresholds.tolist(),
            "precision": precision.tolist(),
            "recall": recall.tolist()
        }
        
        # Save results
        with open('results/stats/roc_analysis.json', 'w') as f:
            json.dump(roc_results, f, indent=2)
            
        # Visualize ROC curve
        plt.figure(figsize=(10, 6))
        
        plt.plot(fpr, tpr, color='blue', lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
        plt.plot([0, 1], [0, 1], color='gray', lw=1, linestyle='--')
        
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic (ROC) Curve')
        plt.legend(loc="lower right")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('figures/stats/roc_curve.png', dpi=300)
        
        # Visualize Precision-Recall curve
        plt.figure(figsize=(10, 6))
        
        plt.plot(recall, precision, color='green', lw=2, label=f'PR curve (AUC = {pr_auc:.3f})')
        plt.plot([0, 1], [0.5, 0.5], color='gray', lw=1, linestyle='--')
        
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Precision-Recall Curve')
        plt.legend(loc="lower left")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('figures/stats/pr_curve.png', dpi=300)
        
        return roc_results
    
    def error_analysis(self):
        """Perform detailed error analysis."""
        logger.info("Performing error analysis")
        
        # Identify false positives and false negatives
        false_positives = self.df_valid[(self.df_valid['ground_truth_binary'] == 0) & 
                                       (self.df_valid['prediction_binary'] == 1)]
        
        false_negatives = self.df_valid[(self.df_valid['ground_truth_binary'] == 1) & 
                                       (self.df_valid['prediction_binary'] == 0)]
        
        # Calculate error rates
        fp_rate = len(false_positives) / len(self.df_valid[self.df_valid['ground_truth_binary'] == 0])
        fn_rate = len(false_negatives) / len(self.df_valid[self.df_valid['ground_truth_binary'] == 1])
        
        # Analyze message characteristics
        fp_message_lengths = false_positives['message'].apply(len)
        fn_message_lengths = false_negatives['message'].apply(len)
        
        all_message_lengths = self.df_valid['message'].apply(len)
        
        # Store results
        error_analysis = {
            "false_positive_rate": fp_rate,
            "false_negative_rate": fn_rate,
            "false_positive_count": len(false_positives),
            "false_negative_count": len(false_negatives),
            "avg_fp_message_length": fp_message_lengths.mean() if len(fp_message_lengths) > 0 else None,
            "avg_fn_message_length": fn_message_lengths.mean() if len(fn_message_lengths) > 0 else None,
            "avg_all_message_length": all_message_lengths.mean(),
            "false_positive_examples": false_positives[['message', 'confidence']].head(5).to_dict('records'),
            "false_negative_examples": false_negatives[['message', 'confidence']].head(5).to_dict('records')
        }
        
        # Save results
        with open('results/stats/error_analysis.json', 'w') as f:
            json.dump(error_analysis, f, indent=2)
            
        # Visualize error rates
        plt.figure(figsize=(8, 6))
        
        error_types = ['False Positive Rate', 'False Negative Rate']
        error_rates = [fp_rate, fn_rate]
        
        bars = plt.bar(error_types, error_rates, color=['orange', 'red'])
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'{height:.2f}', ha='center', va='bottom')
        
        plt.ylim(0, max(error_rates) * 1.2 + 0.05)
        plt.title('Error Rates')
        plt.ylabel('Rate')
        plt.grid(True, axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig('figures/stats/error_rates.png', dpi=300)
        
        # Visualize message length comparison
        plt.figure(figsize=(10, 6))
        
        data = []
        labels = []
        
        if len(fp_message_lengths) > 0:
            data.append(fp_message_lengths)
            labels.append('False Positives')
            
        if len(fn_message_lengths) > 0:
            data.append(fn_message_lengths)
            labels.append('False Negatives')
            
        data.append(all_message_lengths)
        labels.append('All Messages')
        
        plt.boxplot(data, labels=labels, patch_artist=True,
                  boxprops=dict(facecolor='lightblue'),
                  medianprops=dict(color='red'))
        
        plt.ylabel('Message Length (characters)')
        plt.title('Message Length Comparison')
        plt.grid(True, axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig('figures/stats/message_length_comparison.png', dpi=300)
        
        return error_analysis
    
    def generate_statistical_report(self):
        """Generate a comprehensive statistical analysis report."""
        logger.info("Generating statistical analysis report")
        
        # Load results from previous analyses
        try:
            with open('results/stats/confidence_intervals.json', 'r') as f:
                ci_results = json.load(f)
                
            with open('results/stats/hypothesis_tests.json', 'r') as f:
                hypothesis_results = json.load(f)
                
            with open('results/stats/roc_analysis.json', 'r') as f:
                roc_results = json.load(f)
                
            with open('results/stats/error_analysis.json', 'r') as f:
                error_results = json.load(f)
        except Exception as e:
            logger.error(f"Error loading analysis results: {e}")
            return None
        
        # Generate report
        report = f"""# Statistical Analysis Report for Moderation System

## 1. Confidence Intervals

### Accuracy
- Observed Accuracy: {ci_results['accuracy']['observed']:.4f}
- 95% Confidence Interval: [{ci_results['accuracy']['ci_lower']:.4f}, {ci_results['accuracy']['ci_upper']:.4f}]

### Latency
- Mean Latency: {ci_results['latency']['observed']:.2f} seconds
- 95% Confidence Interval: [{ci_results['latency']['ci_lower']:.2f}, {ci_results['latency']['ci_upper']:.2f}] seconds

## 2. Hypothesis Testing

### Accuracy vs. Random Chance
- Null Hypothesis: {hypothesis_results['accuracy_vs_random']['null_hypothesis']}
- p-value: {hypothesis_results['accuracy_vs_random']['p_value']:.4f}
- Result: {hypothesis_results['accuracy_vs_random']['interpretation']}

### Latency vs. Message Length
- Pearson Correlation: r = {hypothesis_results['latency_vs_length']['pearson_r']:.4f}, p = {hypothesis_results['latency_vs_length']['pearson_p']:.4f}
- Spearman Correlation: r = {hypothesis_results['latency_vs_length']['spearman_r']:.4f}, p = {hypothesis_results['latency_vs_length']['spearman_p']:.4f}
- Result: {hypothesis_results['latency_vs_length']['interpretation']}

### Confidence Scores: Correct vs. Incorrect Predictions
- Test: t-test for independent samples
- p-value: {hypothesis_results['confidence_correct_vs_incorrect']['p_value'] if hypothesis_results['confidence_correct_vs_incorrect']['p_value'] is not None else 'N/A'}
- Result: {hypothesis_results['confidence_correct_vs_incorrect']['interpretation']}

## 3. ROC Analysis

- ROC AUC: {roc_results['roc_auc']:.4f}
- PR AUC: {roc_results['pr_auc']:.4f}

## 4. Error Analysis

### Error Rates
- False Positive Rate: {error_results['false_positive_rate']:.4f}
- False Negative Rate: {error_results['false_negative_rate']:.4f}

### Message Length Analysis
- Average Message Length (All): {error_results['avg_all_message_length']:.1f} characters
- Average Message Length (False Positives): {error_results['avg_fp_message_length'] if error_results['avg_fp_message_length'] is not None else 'N/A'} characters
- Average Message Length (False Negatives): {error_results['avg_fn_message_length'] if error_results['avg_fn_message_length'] is not None else 'N/A'} characters

### False Positive Examples
{('\\n'.join([f"- \"{ex['message'][:100]}...\" (confidence: {ex['confidence']:.2f})" for ex in error_results['false_positive_examples']]) if error_results['false_positive_examples'] else 'None')}

### False Negative Examples
{('\\n'.join([f"- \"{ex['message'][:100]}...\" (confidence: {ex['confidence']:.2f})" for ex in error_results['false_negative_examples']]) if error_results['false_negative_examples'] else 'None')}

## 5. Statistical Significance Summary

1. **System Performance**: The moderation system's accuracy of {ci_results['accuracy']['observed']:.4f} is {'' if hypothesis_results['accuracy_vs_random']['significant'] else 'not '}significantly better than random chance (p = {hypothesis_results['accuracy_vs_random']['p_value']:.4f}).

2. **Latency Factors**: Message length is {'' if hypothesis_results['latency_vs_length']['significant'] else 'not '}significantly correlated with processing latency (r = {hypothesis_results['latency_vs_length']['pearson_r']:.4f}, p = {hypothesis_results['latency_vs_length']['pearson_p']:.4f}).

3. **Confidence Reliability**: The system's confidence scores are {'' if hypothesis_results['confidence_correct_vs_incorrect']['significant'] else 'not '}significantly different between correct and incorrect predictions (p = {hypothesis_results['confidence_correct_vs_incorrect']['p_value'] if hypothesis_results['confidence_correct_vs_incorrect']['p_value'] is not None else 'N/A'}).

4. **Error Distribution**: The system shows a higher tendency toward {('false positives' if error_results['false_positive_rate'] > error_results['false_negative_rate'] else 'false negatives') if error_results['false_positive_rate'] is not None and error_results['false_negative_rate'] is not None else 'N/A'}.

## 6. Visualizations

![Confidence Intervals](figures/stats/confidence_intervals.png)
![Latency Correlation](figures/stats/latency_correlation.png)
![ROC Curve](figures/stats/roc_curve.png)
![PR Curve](figures/stats/pr_curve.png)
![Error Rates](figures/stats/error_rates.png)
![Message Length Comparison](figures/stats/message_length_comparison.png)

## 7. Conclusion

This statistical analysis provides strong evidence that the moderation system performs {'' if hypothesis_results['accuracy_vs_random']['significant'] else 'not '}significantly better than random chance in identifying toxic content. The 95% confidence interval for accuracy [{ci_results['accuracy']['ci_lower']:.4f}, {ci_results['accuracy']['ci_upper']:.4f}] indicates the range of expected performance in production environments.

The system's latency shows {'' if hypothesis_results['latency_vs_length']['significant'] else 'no '}significant correlation with message length, suggesting that {'' if hypothesis_results['latency_vs_length']['significant'] else 'factors other than message length are more important determinants of processing time' if hypothesis_results['latency_vs_length']['significant'] else 'processing time increases with message length'}.

The ROC analysis with AUC = {roc_results['roc_auc']:.4f} demonstrates the system's ability to distinguish between toxic and non-toxic content across different threshold settings. The precision-recall curve with AUC = {roc_results['pr_auc']:.4f} further confirms the system's effectiveness in a balanced dataset scenario.

Areas for improvement include addressing the {'higher false positive rate' if error_results['false_positive_rate'] > error_results['false_negative_rate'] else 'higher false negative rate' if error_results['false_positive_rate'] < error_results['false_negative_rate'] else 'balance between false positives and false negatives'}, which would enhance the overall reliability of the moderation system.
"""
        
        # Save report
        with open('results/stats/statistical_report.md', 'w') as f:
            f.write(report)
            
        logger.info("Statistical report saved to 'results/stats/statistical_report.md'")
        return report
    
    def run_analysis(self):
        """Run the complete statistical analysis pipeline."""
        logger.info("Starting statistical analysis pipeline")
        
        # Calculate confidence intervals
        self.confidence_intervals()
        
        # Perform hypothesis testing
        self.hypothesis_testing()
        
        # Perform ROC analysis
        self.roc_analysis()
        
        # Perform error analysis
        self.error_analysis()
        
        # Generate report
        self.generate_statistical_report()
        
        logger.info("Statistical analysis pipeline completed")
        return True

if __name__ == "__main__":
    # Check if results file exists, otherwise use simulated results
    results_path = 'results/moderation_results.json'
    if not os.path.exists(results_path):
        print("Results file not found. Please run moderation_analysis.py first.")
        exit(1)
    
    # Create and run analysis
    stats_analysis = StatisticalAnalysis(results_path)
    stats_analysis.run_analysis()
    
    print("\nStatistical analysis complete! Results saved to 'results/stats' directory.")
    print("Report available at 'results/stats/statistical_report.md'")
    print("Visualizations saved to 'figures/stats' directory")
