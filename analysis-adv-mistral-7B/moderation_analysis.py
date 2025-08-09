#!/usr/bin/env python3
"""
Enhanced Moderation System Analysis Script

This script performs comprehensive analysis of the moderation system using
the experiment-data.csv dataset, including:
- Performance metrics (accuracy, precision, recall, F1)
- Classification report
- ROC curve and Precision-Recall curve
- Confidence intervals
- Latency analysis
- Confidence score analysis
- Tables for dissertation
"""

import os
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score
from scipy import stats
import time
from tqdm import tqdm
import logging
from tabulate import tabulate
import matplotlib.ticker as mtick

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("analysis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create output directories
os.makedirs('results', exist_ok=True)
os.makedirs('figures', exist_ok=True)
os.makedirs('tables', exist_ok=True)

class ModerationAnalysis:
    def __init__(self, data_path='data/processed_dataset.csv'):
        """Initialize with path to the processed dataset."""
        self.data_path = data_path
        self.results = {}
        self.load_data()
        
    def load_data(self):
        """Load and prepare the dataset."""
        logger.info(f"Loading dataset from {self.data_path}")
        
        try:
            # Check if processed data exists, if not, try to load from original
            if not os.path.exists(self.data_path):
                logger.warning(f"Processed dataset not found at {self.data_path}")
                if os.path.exists('experiment-data.csv'):
                    logger.info("Found original experiment-data.csv, preprocessing it now")
                    from preprocess_data import preprocess_data
                    os.makedirs('data', exist_ok=True)
                    self.df = preprocess_data('experiment-data.csv')
                else:
                    logger.error("No dataset found. Please run preprocess_data.py first.")
                    raise FileNotFoundError(f"No dataset found at {self.data_path} or experiment-data.csv")
            else:
                # Load the processed dataset
                self.df = pd.read_csv(self.data_path)
            
            logger.info(f"Loaded {len(self.df)} samples")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def test_moderation_system(self, endpoint="http://localhost:8000/moderate"):
        """Test the moderation system with our dataset."""
        logger.info(f"Testing moderation system at {endpoint}")
        
        # Create test messages
        test_messages = []
        for idx, row in self.df.iterrows():
            test_messages.append({
                "message": row['text'],
                "user_id": f"test_user_{idx}",
                "username": f"TestUser{idx}",
                "channel_id": "evaluation",
                "ground_truth": "toxic" if row['true_label'] == 1 else "non_toxic"
            })
        
        results = []
        for message in tqdm(test_messages, desc="Testing messages"):
            try:
                # Prepare request data
                request_data = {
                    "message": message["message"],
                    "user_id": message["user_id"],
                    "channel_id": message["channel_id"]
                }
                
                # Record start time
                start_time = time.time()
                
                # Make request to moderation system
                import requests
                response = requests.post(endpoint, json=request_data, timeout=30)
                
                # Calculate latency
                latency = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check the decision field from your moderation system
                    decision = result.get("decision", "").lower()
                    is_toxic = decision == "toxic"
                    
                    # Add results
                    results.append({
                        "message": message["message"],
                        "ground_truth": message["ground_truth"],
                        "prediction": "toxic" if is_toxic else "non_toxic",
                        "confidence": result.get("confidence", 0.5),
                        "latency": latency,
                        "message_length": len(message["message"]),
                        "categories": result.get("categories", []),
                        "reasoning": result.get("reasoning", ""),
                        "full_response": result
                    })
                else:
                    logger.warning(f"Error response: {response.status_code} - {response.text}")
                    
                    # Add failed result
                    results.append({
                        "message": message["message"],
                        "ground_truth": message["ground_truth"],
                        "prediction": "error",
                        "confidence": 0,
                        "latency": latency,
                        "message_length": len(message["message"]),
                        "error": f"Status code: {response.status_code}"
                    })
                    
            except Exception as e:
                logger.error(f"Error testing message: {e}")
                
                # Add error result
                results.append({
                    "message": message["message"],
                    "ground_truth": message["ground_truth"],
                    "prediction": "error",
                    "confidence": 0,
                    "latency": 0,
                    "message_length": len(message["message"]),
                    "error": str(e)
                })
        
        # Save results
        with open('results/moderation_results.json', 'w') as f:
            json.dump(results, f, indent=2)
            
        self.moderation_results = results
        return results

    def simulate_moderation_results(self):
        """Simulate moderation results for testing without an actual system."""
        logger.info("Simulating moderation results")
        
        # Create test messages
        test_messages = []
        for idx, row in self.df.iterrows():
            test_messages.append({
                "message": row['text'],
                "user_id": f"test_user_{idx}",
                "username": f"TestUser{idx}",
                "channel_id": "evaluation",
                "ground_truth": "toxic" if row['true_label'] == 1 else "non_toxic"
            })
        
        # Simple keyword-based simulation
        toxic_keywords = ['hideous', 'bizarre', 'assault', 'rape', 'groping', 'stupid', 
                         'idiot', 'hate', 'terrible', 'worst', 'kill', 'die', 'racist',
                         'sexist', 'bigot', 'dumb', 'moron', 'retard', 'crap', 'shit',
                         'fuck', 'damn', 'hell', 'idiot', 'jerk', 'nasty', 'disgusting']
        
        results = []
        for message in tqdm(test_messages, desc="Simulating moderation"):
            # Simple simulation - check for toxic keywords
            text = message["message"].lower()
            toxic_score = sum(1 for keyword in toxic_keywords if keyword in text)
            is_toxic = toxic_score >= 1
            confidence = min(0.5 + (toxic_score * 0.1), 0.95) if is_toxic else max(0.5 - (toxic_score * 0.1), 0.05)
            
            # Simulate latency - higher for longer messages
            base_latency = 0.5
            length_factor = len(text) / 1000
            random_factor = np.random.normal(0, 0.2)
            complexity_factor = 0.2 if toxic_score > 2 else 0.1  # More complex messages take longer
            
            latency = base_latency + length_factor + random_factor + complexity_factor
            
            # Add results
            results.append({
                "message": message["message"],
                "ground_truth": message["ground_truth"],
                "prediction": "toxic" if is_toxic else "non_toxic",
                "confidence": confidence,
                "latency": latency,
                "message_length": len(text),
                "toxic_score": toxic_score
            })
        
        # Save results
        with open('results/moderation_results.json', 'w') as f:
            json.dump(results, f, indent=2)
            
        self.moderation_results = results
        return results
    
    def calculate_metrics(self):
        """Calculate performance metrics from moderation results."""
        # Extract ground truth and predictions
        y_true = [1 if r["ground_truth"] == "toxic" else 0 for r in self.moderation_results]
        y_pred = [1 if r["prediction"] == "toxic" else 0 for r in self.moderation_results]
        
        # Extract confidence scores
        confidences = [r["confidence"] for r in self.moderation_results]
        
        # For ROC curve, we need scores that increase with class 1 probability
        # For toxic predictions, use confidence directly
        # For non-toxic predictions, use 1 - confidence
        y_scores = []
        for i, pred in enumerate(self.moderation_results):
            if pred["prediction"] == "toxic":
                y_scores.append(pred["confidence"])
            else:
                y_scores.append(1 - pred["confidence"])
        
        # Calculate basic metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        cm = confusion_matrix(y_true, y_pred).tolist()
        
        # Calculate ROC curve and AUC
        fpr, tpr, _ = roc_curve(y_true, y_scores)
        roc_auc = auc(fpr, tpr)
        
        # Calculate Precision-Recall curve and AUC
        precision_curve, recall_curve, _ = precision_recall_curve(y_true, y_scores)
        pr_auc = auc(recall_curve, precision_curve)
        avg_precision = average_precision_score(y_true, y_scores)
        
        # Calculate latency statistics
        latencies = [r["latency"] for r in self.moderation_results]
        avg_latency = np.mean(latencies)
        median_latency = np.median(latencies)
        std_latency = np.std(latencies)
        min_latency = np.min(latencies)
        max_latency = np.max(latencies)
        
        # Calculate confidence interval for accuracy using bootstrap
        n_bootstrap = 1000
        bootstrap_accuracies = []
        
        for _ in range(n_bootstrap):
            # Sample with replacement
            indices = np.random.choice(len(y_true), size=len(y_true), replace=True)
            y_true_sample = [y_true[i] for i in indices]
            y_pred_sample = [y_pred[i] for i in indices]
            bootstrap_accuracies.append(accuracy_score(y_true_sample, y_pred_sample))
        
        # Calculate 95% confidence interval
        ci_lower = np.percentile(bootstrap_accuracies, 2.5)
        ci_upper = np.percentile(bootstrap_accuracies, 97.5)
        
        # Get classification report as dictionary
        class_report = classification_report(y_true, y_pred, output_dict=True)
        
        # Store all metrics
        metrics = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "confusion_matrix": cm,
            "roc_auc": roc_auc,
            "pr_auc": pr_auc,
            "avg_precision": avg_precision,
            "fpr": fpr.tolist(),
            "tpr": tpr.tolist(),
            "precision_curve": precision_curve.tolist(),
            "recall_curve": recall_curve.tolist(),
            "sample_count": len(y_true),
            "avg_latency": avg_latency,
            "median_latency": median_latency,
            "std_latency": std_latency,
            "min_latency": min_latency,
            "max_latency": max_latency,
            "accuracy_ci_lower": ci_lower,
            "accuracy_ci_upper": ci_upper,
            "classification_report": class_report
        }
        
        # Save metrics
        with open('results/performance_metrics.json', 'w') as f:
            json.dump(metrics, f, indent=2)
            
        self.metrics = metrics
        return metrics
    
    def generate_visualizations(self):
        """Generate visualizations of the results."""
        logger.info("Generating visualizations")
        
        # Set style
        sns.set(style="whitegrid")
        plt.rcParams.update({'font.size': 12})
        
        # 1. Confusion Matrix
        plt.figure(figsize=(8, 6))
        cm = np.array(self.metrics["confusion_matrix"])
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=['Non-Toxic', 'Toxic'],
                   yticklabels=['Non-Toxic', 'Toxic'])
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.title('Confusion Matrix')
        plt.tight_layout()
        plt.savefig('figures/confusion_matrix.png', dpi=300)
        
        # 2. Performance Metrics Bar Chart
        plt.figure(figsize=(10, 6))
        metrics_to_plot = ['accuracy', 'precision', 'recall', 'f1']
        values = [self.metrics[m] for m in metrics_to_plot]
        
        bars = plt.bar(metrics_to_plot, values, color='skyblue')
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'{height:.2f}', ha='center', va='bottom')
        
        plt.ylim(0, 1.1)
        plt.title('Moderation System Performance Metrics')
        plt.tight_layout()
        plt.savefig('figures/performance_metrics.png', dpi=300)
        
        # 3. ROC Curve
        plt.figure(figsize=(8, 6))
        plt.plot(self.metrics["fpr"], self.metrics["tpr"], color='darkorange', lw=2,
                label=f'ROC curve (AUC = {self.metrics["roc_auc"]:.2f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic (ROC) Curve')
        plt.legend(loc="lower right")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('figures/roc_curve.png', dpi=300)
        
        # 4. Precision-Recall Curve
        plt.figure(figsize=(8, 6))
        plt.plot(self.metrics["recall_curve"], self.metrics["precision_curve"], color='green', lw=2,
                label=f'PR curve (AUC = {self.metrics["pr_auc"]:.2f})')
        plt.axhline(y=sum(y_true := [1 if r["ground_truth"] == "toxic" else 0 for r in self.moderation_results]) / len(y_true), 
                   color='red', linestyle='--', label=f'Baseline (No Skill)')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Precision-Recall Curve')
        plt.legend(loc="lower left")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('figures/precision_recall_curve.png', dpi=300)
        
        # 5. Latency Distribution
        plt.figure(figsize=(10, 6))
        latencies = [r["latency"] for r in self.moderation_results]
        
        sns.histplot(latencies, kde=True, color='skyblue')
        plt.axvline(self.metrics["avg_latency"], color='red', linestyle='--', 
                   label=f'Mean: {self.metrics["avg_latency"]:.2f}s')
        plt.axvline(self.metrics["median_latency"], color='green', linestyle='--', 
                   label=f'Median: {self.metrics["median_latency"]:.2f}s')
        
        plt.xlabel('Latency (seconds)')
        plt.ylabel('Frequency')
        plt.title('Moderation System Latency Distribution')
        plt.legend()
        plt.tight_layout()
        plt.savefig('figures/latency_distribution.png', dpi=300)
        
        # 6. Latency vs Message Length
        plt.figure(figsize=(10, 6))
        
        message_lengths = [r["message_length"] for r in self.moderation_results]
        latencies = [r["latency"] for r in self.moderation_results]
        
        plt.scatter(message_lengths, latencies, alpha=0.6, color='blue')
        
        # Add trend line
        z = np.polyfit(message_lengths, latencies, 1)
        p = np.poly1d(z)
        plt.plot(message_lengths, p(message_lengths), "r--", alpha=0.8)
        
        plt.xlabel('Message Length (characters)')
        plt.ylabel('Latency (seconds)')
        plt.title('Latency vs Message Length')
        plt.tight_layout()
        plt.savefig('figures/latency_vs_length.png', dpi=300)
        
        # 7. Confidence Score Distribution
        plt.figure(figsize=(10, 6))
        
        toxic_conf = [r["confidence"] for r in self.moderation_results if r["prediction"] == "toxic"]
        non_toxic_conf = [r["confidence"] for r in self.moderation_results if r["prediction"] == "non_toxic"]
        
        sns.kdeplot(toxic_conf, label='Toxic', color='red', fill=True, alpha=0.3)
        sns.kdeplot(non_toxic_conf, label='Non-Toxic', color='green', fill=True, alpha=0.3)
        
        plt.xlabel('Confidence Score')
        plt.ylabel('Density')
        plt.title('Confidence Score Distribution by Predicted Class')
        plt.legend()
        plt.tight_layout()
        plt.savefig('figures/confidence_distribution.png', dpi=300)
        
        # 8. Accuracy with Confidence Interval
        plt.figure(figsize=(8, 6))
        
        plt.bar(['Accuracy'], [self.metrics["accuracy"]], color='skyblue', yerr=[[self.metrics["accuracy"] - self.metrics["accuracy_ci_lower"]], 
                                                                               [self.metrics["accuracy_ci_upper"] - self.metrics["accuracy"]]], 
               capsize=10)
        
        plt.text(0, self.metrics["accuracy"] + 0.02, f'{self.metrics["accuracy"]:.2f}', ha='center')
        plt.text(0, self.metrics["accuracy"] - 0.08, f'95% CI: [{self.metrics["accuracy_ci_lower"]:.2f}, {self.metrics["accuracy_ci_upper"]:.2f}]', ha='center')
        
        plt.ylim(0, 1.1)
        plt.title('Accuracy with 95% Confidence Interval')
        plt.tight_layout()
        plt.savefig('figures/accuracy_confidence_interval.png', dpi=300)
        
        # 9. Latency Metrics Chart
        plt.figure(figsize=(10, 6))
        
        latency_metrics = ['avg_latency', 'median_latency', 'min_latency', 'max_latency']
        latency_values = [self.metrics[m] for m in latency_metrics]
        latency_labels = ['Average', 'Median', 'Minimum', 'Maximum']
        
        bars = plt.bar(latency_labels, latency_values, color=['skyblue', 'lightgreen', 'lightcoral', 'orange'])
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'{height:.2f}s', ha='center', va='bottom')
        
        plt.ylabel('Latency (seconds)')
        plt.title('Moderation System Latency Metrics')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig('figures/latency_metrics.png', dpi=300)
        
        logger.info("Visualizations saved to 'figures' directory")
    
    def generate_tables(self):
        """Generate tables for the dissertation."""
        logger.info("Generating tables for dissertation")
        
        # 1. Performance Metrics Table
        performance_table = [
            ["Metric", "Value", "95% Confidence Interval"],
            ["Accuracy", f"{self.metrics['accuracy']:.4f}", f"[{self.metrics['accuracy_ci_lower']:.4f}, {self.metrics['accuracy_ci_upper']:.4f}]"],
            ["Precision", f"{self.metrics['precision']:.4f}", "N/A"],
            ["Recall", f"{self.metrics['recall']:.4f}", "N/A"],
            ["F1 Score", f"{self.metrics['f1']:.4f}", "N/A"],
            ["ROC AUC", f"{self.metrics['roc_auc']:.4f}", "N/A"],
            ["PR AUC", f"{self.metrics['pr_auc']:.4f}", "N/A"]
        ]
        
        with open('tables/performance_metrics_table.md', 'w') as f:
            f.write(tabulate(performance_table, headers="firstrow", tablefmt="pipe"))
        
        # 2. Confusion Matrix Table
        cm = self.metrics["confusion_matrix"]
        confusion_table = [
            ["", "Predicted Non-Toxic", "Predicted Toxic"],
            ["Actual Non-Toxic", cm[0][0], cm[0][1]],
            ["Actual Toxic", cm[1][0], cm[1][1]]
        ]
        
        with open('tables/confusion_matrix_table.md', 'w') as f:
            f.write(tabulate(confusion_table, headers="firstrow", tablefmt="pipe"))
        
        # 3. Classification Report Table
        report = self.metrics["classification_report"]
        class_report_table = [
            ["Class", "Precision", "Recall", "F1-Score", "Support"],
            ["Non-Toxic (0)", f"{report['0']['precision']:.4f}", f"{report['0']['recall']:.4f}", f"{report['0']['f1-score']:.4f}", f"{report['0']['support']}"],
            ["Toxic (1)", f"{report['1']['precision']:.4f}", f"{report['1']['recall']:.4f}", f"{report['1']['f1-score']:.4f}", f"{report['1']['support']}"],
            ["Accuracy", "", "", f"{report['accuracy']:.4f}", f"{report['macro avg']['support']}"],
            ["Macro Avg", f"{report['macro avg']['precision']:.4f}", f"{report['macro avg']['recall']:.4f}", f"{report['macro avg']['f1-score']:.4f}", f"{report['macro avg']['support']}"],
            ["Weighted Avg", f"{report['weighted avg']['precision']:.4f}", f"{report['weighted avg']['recall']:.4f}", f"{report['weighted avg']['f1-score']:.4f}", f"{report['weighted avg']['support']}"]
        ]
        
        with open('tables/classification_report_table.md', 'w') as f:
            f.write(tabulate(class_report_table, headers="firstrow", tablefmt="pipe"))
        
        # 4. Latency Metrics Table
        latency_table = [
            ["Latency Metric", "Value (seconds)"],
            ["Average", f"{self.metrics['avg_latency']:.4f}"],
            ["Median", f"{self.metrics['median_latency']:.4f}"],
            ["Standard Deviation", f"{self.metrics['std_latency']:.4f}"],
            ["Minimum", f"{self.metrics['min_latency']:.4f}"],
            ["Maximum", f"{self.metrics['max_latency']:.4f}"]
        ]
        
        with open('tables/latency_metrics_table.md', 'w') as f:
            f.write(tabulate(latency_table, headers="firstrow", tablefmt="pipe"))
        
        # 5. Dataset Summary Table
        toxic_count = sum(1 for r in self.moderation_results if r["ground_truth"] == "toxic")
        non_toxic_count = sum(1 for r in self.moderation_results if r["ground_truth"] == "non_toxic")
        
        dataset_table = [
            ["Category", "Count", "Percentage"],
            ["Toxic", f"{toxic_count}", f"{toxic_count/len(self.moderation_results)*100:.1f}%"],
            ["Non-Toxic", f"{non_toxic_count}", f"{non_toxic_count/len(self.moderation_results)*100:.1f}%"],
            ["Total", f"{len(self.moderation_results)}", "100.0%"]
        ]
        
        with open('tables/dataset_summary_table.md', 'w') as f:
            f.write(tabulate(dataset_table, headers="firstrow", tablefmt="pipe"))
        
        logger.info("Tables saved to 'tables' directory")
    
    def generate_report(self):
        """Generate a comprehensive analysis report."""
        logger.info("Generating analysis report")
        
        report = f"""# Moderation System Analysis Report

## Dataset Summary

The analysis was conducted using a dataset of {len(self.moderation_results)} messages, with the following distribution:

{open('tables/dataset_summary_table.md').read()}

## Performance Metrics

The moderation system achieved the following performance metrics:

{open('tables/performance_metrics_table.md').read()}

## Classification Report

Detailed classification metrics by class:

{open('tables/classification_report_table.md').read()}

## Confusion Matrix

The confusion matrix shows the distribution of predictions versus actual labels:

{open('tables/confusion_matrix_table.md').read()}

## Latency Analysis

The system demonstrated the following latency characteristics:

{open('tables/latency_metrics_table.md').read()}

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

- **Accuracy**: The moderation system achieved {self.metrics['accuracy']:.1%} accuracy (95% CI: [{self.metrics['accuracy_ci_lower']:.1%}, {self.metrics['accuracy_ci_upper']:.1%}]) on the test dataset.
- **Precision**: The system shows a {self.metrics['precision']:.1%} precision rate for toxic content detection.
- **Recall**: The recall rate of {self.metrics['recall']:.1%} indicates the system's ability to identify toxic content.
- **F1 Score**: The F1 score of {self.metrics['f1']:.4f} represents the harmonic mean of precision and recall.
- **ROC AUC**: The area under the ROC curve of {self.metrics['roc_auc']:.4f} demonstrates the system's ability to discriminate between classes.
- **PR AUC**: The area under the Precision-Recall curve of {self.metrics['pr_auc']:.4f} shows the trade-off between precision and recall.

## Conclusion

This analysis demonstrates the effectiveness of the real-time moderation system in identifying toxic content in chat messages. The system shows {self.metrics['accuracy']:.1%} accuracy with the experiment dataset of toxic and non-toxic messages.

The latency analysis indicates an average processing time of {self.metrics['avg_latency']:.2f} seconds per message, which is suitable for real-time applications. Further optimization could focus on reducing the standard deviation of {self.metrics['std_latency']:.2f} seconds to provide more consistent response times.

Areas for improvement include reducing false positives ({self.metrics['confusion_matrix'][0][1]} instances) and false negatives ({self.metrics['confusion_matrix'][1][0]} instances) to enhance the overall reliability of the moderation system.
"""
        
        # Save report
        with open('results/analysis_report.md', 'w') as f:
            f.write(report)
            
        logger.info("Analysis report saved to 'results/analysis_report.md'")
        return report
    
    def run_analysis(self, use_real_system=False):
        """Run the complete analysis pipeline."""
        logger.info("Starting analysis pipeline")
        
        # Test moderation system (real or simulated)
        if use_real_system:
            logger.info("Using real moderation system endpoint")
            self.test_moderation_system()
        else:
            logger.info("Using simulated moderation results")
            self.simulate_moderation_results()
        
        # Calculate metrics
        self.calculate_metrics()
        
        # Generate tables
        self.generate_tables()
        
        # Generate visualizations
        self.generate_visualizations()
        
        # Generate report
        self.generate_report()
        
        logger.info("Analysis pipeline completed")
        return self.metrics

if __name__ == "__main__":
    # Create and run analysis
    analysis = ModerationAnalysis()
    analysis.run_analysis(use_real_system=True)  # Changed to True to use DeepSeek LLM endpoint
    
    print("\nAnalysis complete! Results saved to 'results' directory.")
    print("Report available at 'results/analysis_report.md'")
    print("Visualizations saved to 'figures' directory")
    print("Tables saved to 'tables' directory")
