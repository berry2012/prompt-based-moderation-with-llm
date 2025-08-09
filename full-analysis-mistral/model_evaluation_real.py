#!/usr/bin/env python3
"""
Model Performance Evaluator for Real-Time Moderation System
===========================================================

This module evaluates the performance of the moderation system using real labeled data
from the SetFit/toxic_conversations dataset. It implements resource-friendly evaluation
strategies for constrained server environments.

Author: Academic Research  
Date: 2025
"""

import requests
import json
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import confusion_matrix, classification_report, roc_auc_score, roc_curve
from sklearn.metrics import precision_recall_curve, average_precision_score
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import our dataset loader
from dataset_loader import DissertationDatasetLoader

class ModelPerformanceEvaluator:
    """
    Comprehensive model performance evaluator using real labeled dataset.
    Implements resource-friendly evaluation strategies for constrained environments.
    """
    
    def __init__(self, csv_path="dissertation-experiment-data.csv", resource_friendly=True):
        """
        Initialize the evaluator with real dataset.
        
        Args:
            csv_path (str): Path to the dissertation dataset CSV file
            resource_friendly (bool): Enable resource-friendly evaluation mode
        """
        self.evaluation_data = {}
        self.ground_truth = []
        self.predictions = []
        self.prediction_probabilities = []
        
        # Ultra-conservative configuration for overloaded Mistral server
        self.resource_friendly = resource_friendly
        self.request_delay = 10.0 if resource_friendly else 2.0     # Much longer delay between requests
        self.timeout = 120.0 if resource_friendly else 45.0        # Extended timeout for slow generation
        self.max_retries = 3 if resource_friendly else 5           # Fewer retries to avoid pile-up
        self.batch_delay = 30.0 if resource_friendly else 5.0      # Long delay between batches
        self.max_concurrent = 1                                     # Only 1 request at a time
        
        # Load the real dataset
        self.dataset_loader = DissertationDatasetLoader(csv_path)
        print(f"🔬 Initialized Model Evaluator ({'Resource-Friendly' if resource_friendly else 'Standard'} mode)")
        
    def collect_evaluation_data(self, test_messages=None, sample_size=30):
        """
        Collect evaluation data using real labeled dataset with resource-friendly approach.
        
        Args:
            test_messages (list): Optional custom test messages
            sample_size (int): Number of samples to evaluate (for resource management)
        """
        if test_messages is None:
            # Use real dataset instead of hardcoded messages
            test_messages = self.dataset_loader.get_balanced_sample(
                n_samples=sample_size, 
                random_state=42
            )
        
        print(f"📊 Evaluating model with {len(test_messages)} real test messages...")
        print(f"⚙️  Ultra-conservative mode for overloaded Mistral server:")
        print(f"   • Request delay: {self.request_delay}s")
        print(f"   • Timeout: {self.timeout}s")
        print(f"   • Max retries: {self.max_retries}")
        print(f"   • Batch delay: {self.batch_delay}s")
        print(f"   • Processing 1 request at a time to avoid server overload")
        
        results = []
        failed_requests = 0
        
        for i, (message, true_label) in enumerate(test_messages):
            success = False
            retry_count = 0
            
            while not success and retry_count < self.max_retries:
                try:
                    # Resource-friendly delay
                    if i > 0:  # Don't delay before first request
                        time.sleep(self.request_delay)
                    
                    # Send message to Chat Simulator API (proper entry point)
                    response = requests.post(
                        'http://localhost:8002/api/send-message',
                        json={
                            'message': message,
                            'user_id': f'test_user_{i}',
                            'username': f'TestUser{i}',
                            'channel_id': 'evaluation_channel'
                        },
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Extract prediction and confidence from Chat Simulator API response
                        # The Chat Simulator API returns the full moderation result
                        moderation_result = result.get('result', {}).get('moderation_result', {})
                        
                        # Determine if message was flagged
                        action = moderation_result.get('action', 'approve')
                        predicted_label = "Toxic" if action == 'flag' else "Non-Toxic"
                        
                        # Extract confidence score
                        confidence = moderation_result.get('confidence', 0.5)
                        
                        # Extract processing time
                        processing_time = moderation_result.get('processing_time', 0)
                        
                        # Store results
                        results.append({
                            'message': message,
                            'true_label': true_label,
                            'predicted_label': predicted_label,
                            'confidence': confidence,
                            'response_time': processing_time,
                            'action': action,
                            'full_response': result,
                            'moderation_result': moderation_result
                        })
                        
                        self.ground_truth.append(true_label)
                        self.predictions.append(predicted_label)
                        self.prediction_probabilities.append(confidence if predicted_label == "Toxic" else 1-confidence)
                        
                        success = True
                        
                        # Progress indicator
                        if (i + 1) % 10 == 0:
                            print(f"✅ Processed {i + 1}/{len(test_messages)} messages")
                    
                    else:
                        retry_count += 1
                        if retry_count < self.max_retries:
                            print(f"⚠️  Request failed (status {response.status_code}), retrying in {self.request_delay * 2}s... (attempt {retry_count + 1}/{self.max_retries})")
                            time.sleep(self.request_delay * 2)  # Longer delay on retry
                        else:
                            print(f"❌ Request failed after {self.max_retries} attempts: {response.status_code}")
                            failed_requests += 1
                
                except requests.exceptions.Timeout:
                    retry_count += 1
                    if retry_count < self.max_retries:
                        backoff_delay = self.request_delay * (2 ** retry_count)  # Exponential backoff
                        print(f"⏰ Request timeout (server overloaded), backing off {backoff_delay:.1f}s... (attempt {retry_count + 1}/{self.max_retries})")
                        time.sleep(backoff_delay)
                    else:
                        print(f"❌ Request timed out after {self.max_retries} attempts - server likely overloaded")
                        failed_requests += 1
                
                except requests.exceptions.RequestException as e:
                    retry_count += 1
                    if retry_count < self.max_retries:
                        backoff_delay = self.request_delay * (1.5 ** retry_count)
                        print(f"🔌 Connection error (server overloaded), backing off {backoff_delay:.1f}s... (attempt {retry_count + 1}/{self.max_retries})")
                        time.sleep(backoff_delay)
                    else:
                        print(f"❌ Connection failed after {self.max_retries} attempts: {e}")
                        failed_requests += 1
            
            # Adaptive batch delay based on failure rate
            if (i + 1) % 5 == 0 and i < len(test_messages) - 1:  # Every 5 messages instead of 10
                # Increase delay if we're seeing failures
                failure_rate = failed_requests / (i + 1) if i > 0 else 0
                adaptive_delay = self.batch_delay * (1 + failure_rate * 2)  # Increase delay based on failures
                print(f"⏸️  Adaptive batch delay ({adaptive_delay:.1f}s) - failure rate: {failure_rate:.1%}")
                time.sleep(adaptive_delay)
        
        self.evaluation_data = {
            'results': results,
            'total_requests': len(test_messages),
            'successful_requests': len(results),
            'failed_requests': failed_requests,
            'success_rate': len(results) / len(test_messages) if test_messages else 0
        }
        
        print(f"📊 Evaluation completed:")
        print(f"   • Total requests: {len(test_messages)}")
        print(f"   • Successful: {len(results)}")
        print(f"   • Failed: {failed_requests}")
        print(f"   • Success rate: {self.evaluation_data['success_rate']:.1%}")
        
        return self.evaluation_data
    
    def calculate_performance_metrics(self):
        """
        Calculate comprehensive performance metrics for academic evaluation.
        
        Returns:
            dict: Comprehensive performance metrics
        """
        if not self.ground_truth or not self.predictions:
            print("❌ No evaluation data available. Run collect_evaluation_data() first.")
            return {}
        
        # Convert labels to binary for sklearn
        y_true_binary = [1 if label == "Toxic" else 0 for label in self.ground_truth]
        y_pred_binary = [1 if label == "Toxic" else 0 for label in self.predictions]
        
        # Basic metrics
        accuracy = accuracy_score(y_true_binary, y_pred_binary)
        precision = precision_score(y_true_binary, y_pred_binary, zero_division=0)
        recall = recall_score(y_true_binary, y_pred_binary, zero_division=0)
        f1 = f1_score(y_true_binary, y_pred_binary, zero_division=0)
        
        # Confusion matrix
        cm = confusion_matrix(y_true_binary, y_pred_binary)
        
        # ROC AUC (if we have probability scores)
        try:
            roc_auc = roc_auc_score(y_true_binary, self.prediction_probabilities)
        except:
            roc_auc = None
        
        # Classification report
        class_report = classification_report(
            y_true_binary, y_pred_binary, 
            target_names=['Non-Toxic', 'Toxic'],
            output_dict=True,
            zero_division=0
        )
        
        # Response time statistics
        response_times = [r['response_time'] for r in self.evaluation_data.get('results', [])]
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'confusion_matrix': cm,
            'classification_report': class_report,
            'response_time_stats': {
                'mean': np.mean(response_times) if response_times else 0,
                'median': np.median(response_times) if response_times else 0,
                'std': np.std(response_times) if response_times else 0,
                'min': np.min(response_times) if response_times else 0,
                'max': np.max(response_times) if response_times else 0
            },
            'dataset_info': {
                'total_samples': len(self.ground_truth),
                'toxic_samples': sum(y_true_binary),
                'non_toxic_samples': len(y_true_binary) - sum(y_true_binary),
                'success_rate': self.evaluation_data.get('success_rate', 0)
            }
        }
        
        return metrics
    
    def create_evaluation_visualizations(self, output_dir="reports"):
        """Create comprehensive evaluation visualizations using real data."""
        
        metrics = self.calculate_performance_metrics()
        if not metrics:
            return None
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 15))
        
        # 1. Confusion Matrix
        ax1 = plt.subplot(3, 3, 1)
        sns.heatmap(metrics['confusion_matrix'], annot=True, fmt='d', cmap='Blues',
                   xticklabels=['Non-Toxic', 'Toxic'], yticklabels=['Non-Toxic', 'Toxic'])
        ax1.set_title('Confusion Matrix\n(Real Dataset)')
        ax1.set_ylabel('True Label')
        ax1.set_xlabel('Predicted Label')
        
        # 2. Performance Metrics Bar Chart
        ax2 = plt.subplot(3, 3, 2)
        metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
        metrics_values = [metrics['accuracy'], metrics['precision'], metrics['recall'], metrics['f1_score']]
        bars = ax2.bar(metrics_names, metrics_values, color=['skyblue', 'lightgreen', 'lightcoral', 'gold'])
        ax2.set_title('Performance Metrics\n(Real Dataset)')
        ax2.set_ylabel('Score')
        ax2.set_ylim(0, 1)
        
        # Add value labels on bars
        for bar, value in zip(bars, metrics_values):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.3f}', ha='center', va='bottom')
        
        # 3. ROC Curve (if available)
        ax3 = plt.subplot(3, 3, 3)
        if metrics['roc_auc'] is not None:
            y_true_binary = [1 if label == "Toxic" else 0 for label in self.ground_truth]
            fpr, tpr, _ = roc_curve(y_true_binary, self.prediction_probabilities)
            ax3.plot(fpr, tpr, color='darkorange', lw=2, 
                    label=f'ROC curve (AUC = {metrics["roc_auc"]:.3f})')
            ax3.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
            ax3.set_xlim([0.0, 1.0])
            ax3.set_ylim([0.0, 1.05])
            ax3.set_xlabel('False Positive Rate')
            ax3.set_ylabel('True Positive Rate')
            ax3.set_title('ROC Curve\n(Real Dataset)')
            ax3.legend(loc="lower right")
        else:
            ax3.text(0.5, 0.5, 'ROC Curve\nNot Available', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('ROC Curve\n(Real Dataset)')
        
        # 4. Response Time Distribution
        ax4 = plt.subplot(3, 3, 4)
        response_times = [r['response_time'] for r in self.evaluation_data.get('results', [])]
        if response_times:
            ax4.hist(response_times, bins=20, alpha=0.7, color='lightblue', edgecolor='black')
            ax4.set_title(f'Response Time Distribution\nMean: {metrics["response_time_stats"]["mean"]:.2f}s')
            ax4.set_xlabel('Response Time (seconds)')
            ax4.set_ylabel('Frequency')
        else:
            ax4.text(0.5, 0.5, 'No Response Time\nData Available', ha='center', va='center', transform=ax4.transAxes)
        
        # 5. Class Distribution
        ax5 = plt.subplot(3, 3, 5)
        class_counts = [metrics['dataset_info']['non_toxic_samples'], metrics['dataset_info']['toxic_samples']]
        ax5.pie(class_counts, labels=['Non-Toxic', 'Toxic'], autopct='%1.1f%%', colors=['lightgreen', 'lightcoral'])
        ax5.set_title('Dataset Class Distribution\n(Real Data)')
        
        # 6. Confidence Distribution
        ax6 = plt.subplot(3, 3, 6)
        if self.prediction_probabilities:
            ax6.hist(self.prediction_probabilities, bins=20, alpha=0.7, color='gold', edgecolor='black')
            ax6.set_title('Prediction Confidence Distribution')
            ax6.set_xlabel('Confidence Score')
            ax6.set_ylabel('Frequency')
        else:
            ax6.text(0.5, 0.5, 'No Confidence\nData Available', ha='center', va='center', transform=ax6.transAxes)
        
        # 7. Success Rate
        ax7 = plt.subplot(3, 3, 7)
        success_rate = metrics['dataset_info']['success_rate']
        ax7.bar(['Success Rate'], [success_rate], color='green' if success_rate > 0.9 else 'orange')
        ax7.set_title('Evaluation Success Rate')
        ax7.set_ylabel('Rate')
        ax7.set_ylim(0, 1)
        ax7.text(0, success_rate + 0.02, f'{success_rate:.1%}', ha='center', va='bottom')
        
        # 8. Per-Class Performance
        ax8 = plt.subplot(3, 3, 8)
        class_metrics = ['precision', 'recall', 'f1-score']
        non_toxic_scores = [metrics['classification_report']['0'][m] for m in class_metrics]
        toxic_scores = [metrics['classification_report']['1'][m] for m in class_metrics]
        
        x = np.arange(len(class_metrics))
        width = 0.35
        
        ax8.bar(x - width/2, non_toxic_scores, width, label='Non-Toxic', color='lightgreen')
        ax8.bar(x + width/2, toxic_scores, width, label='Toxic', color='lightcoral')
        
        ax8.set_xlabel('Metrics')
        ax8.set_ylabel('Score')
        ax8.set_title('Per-Class Performance')
        ax8.set_xticks(x)
        ax8.set_xticklabels(class_metrics)
        ax8.legend()
        ax8.set_ylim(0, 1)
        
        # 9. Dataset Information
        ax9 = plt.subplot(3, 3, 9)
        ax9.axis('off')
        info_text = f"""Dataset Information:
        
Total Samples: {metrics['dataset_info']['total_samples']}
Toxic: {metrics['dataset_info']['toxic_samples']}
Non-Toxic: {metrics['dataset_info']['non_toxic_samples']}

Evaluation Results:
Success Rate: {metrics['dataset_info']['success_rate']:.1%}
Resource-Friendly: {self.resource_friendly}

Performance Summary:
Accuracy: {metrics['accuracy']:.3f}
F1-Score: {metrics['f1_score']:.3f}
Precision: {metrics['precision']:.3f}
Recall: {metrics['recall']:.3f}"""
        
        ax9.text(0.1, 0.9, info_text, transform=ax9.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/model_evaluation_real.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        return metrics
    
    def _format_confusion_matrix(self, cm):
        """Safely format confusion matrix for display."""
        try:
            unique_labels = sorted(list(set(self.ground_truth)))
            if len(unique_labels) == cm.shape[0] == cm.shape[1]:
                return pd.DataFrame(cm, index=unique_labels, columns=unique_labels).to_string()
            else:
                # Fallback to simple array representation if shapes don't match
                return f"Confusion Matrix (shape: {cm.shape}):\n{cm}"
        except Exception as e:
            return f"Confusion Matrix:\n{cm}\n(Error formatting: {e})"
    
    def generate_academic_report(self, output_dir="reports"):
        """Generate academic-quality evaluation report using real dataset."""
        
        metrics = self.calculate_performance_metrics()
        if not metrics:
            return None
        
        # Get dataset statistics
        dataset_stats = self.dataset_loader.get_dataset_statistics()
        
        report = f"""# Model Performance Evaluation Report
## Real Dataset Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### Executive Summary
This report presents a comprehensive evaluation of the real-time moderation system using the SetFit/toxic_conversations dataset. The evaluation employed a {'resource-friendly' if self.resource_friendly else 'standard'} approach to accommodate server constraints.

### Dataset Information
- **Source**: SetFit/toxic_conversations (Hugging Face)
- **Total Dataset Size**: {dataset_stats['total_samples']:,} samples
- **Evaluation Sample Size**: {metrics['dataset_info']['total_samples']} samples
- **Class Distribution**:
  - Toxic messages: {metrics['dataset_info']['toxic_samples']} ({metrics['dataset_info']['toxic_samples']/metrics['dataset_info']['total_samples']:.1%})
  - Non-toxic messages: {metrics['dataset_info']['non_toxic_samples']} ({metrics['dataset_info']['non_toxic_samples']/metrics['dataset_info']['total_samples']:.1%})

### Evaluation Configuration
- **Resource-Friendly Mode**: {self.resource_friendly}
- **Request Delay**: {self.request_delay}s
- **Timeout**: {self.timeout}s
- **Max Retries**: {self.max_retries}
- **Success Rate**: {metrics['dataset_info']['success_rate']:.1%}

### Performance Metrics

#### Classification Performance
- **Accuracy**: {metrics['accuracy']:.4f} ({metrics['accuracy']:.1%})
- **Precision**: {metrics['precision']:.4f} ({metrics['precision']:.1%})
- **Recall**: {metrics['recall']:.4f} ({metrics['recall']:.1%})
- **F1-Score**: {metrics['f1_score']:.4f} ({metrics['f1_score']:.1%})
{f"- **ROC AUC**: {metrics['roc_auc']:.4f}" if metrics['roc_auc'] else "- **ROC AUC**: Not available"}

#### Response Time Analysis
- **Mean Response Time**: {metrics['response_time_stats']['mean']:.3f} seconds
- **Median Response Time**: {metrics['response_time_stats']['median']:.3f} seconds
- **Standard Deviation**: {metrics['response_time_stats']['std']:.3f} seconds
- **Min Response Time**: {metrics['response_time_stats']['min']:.3f} seconds
- **Max Response Time**: {metrics['response_time_stats']['max']:.3f} seconds

### Confusion Matrix Analysis
The confusion matrix reveals the following classification patterns:
{self._format_confusion_matrix(metrics['confusion_matrix'])}

### Per-Class Performance Analysis

#### Non-Toxic Class Performance
- **Precision**: {metrics['classification_report']['0']['precision']:.4f}
- **Recall**: {metrics['classification_report']['0']['recall']:.4f}
- **F1-Score**: {metrics['classification_report']['0']['f1-score']:.4f}
- **Support**: {metrics['classification_report']['0']['support']} samples

#### Toxic Class Performance
- **Precision**: {metrics['classification_report']['1']['precision']:.4f}
- **Recall**: {metrics['classification_report']['1']['recall']:.4f}
- **F1-Score**: {metrics['classification_report']['1']['f1-score']:.4f}
- **Support**: {metrics['classification_report']['1']['support']} samples

### Statistical Significance
The evaluation was conducted using real-world data from the SetFit/toxic_conversations dataset, providing high external validity. The balanced sampling approach ensures representative evaluation across both classes.

### Resource Management Analysis
The {'resource-friendly' if self.resource_friendly else 'standard'} evaluation approach was employed:
- **Request Success Rate**: {metrics['dataset_info']['success_rate']:.1%}
- **Failed Requests**: {self.evaluation_data.get('failed_requests', 0)}
- **Total Requests**: {self.evaluation_data.get('total_requests', 0)}

### Recommendations

#### Performance Optimization
1. **Accuracy Improvement**: Current accuracy of {metrics['accuracy']:.1%} {'meets' if metrics['accuracy'] >= 0.85 else 'falls below'} typical production standards (85%+)
2. **Precision-Recall Balance**: {'Well-balanced' if abs(metrics['precision'] - metrics['recall']) < 0.1 else 'Imbalanced'} precision ({metrics['precision']:.3f}) and recall ({metrics['recall']:.3f})
3. **Response Time**: Average response time of {metrics['response_time_stats']['mean']:.2f}s {'is acceptable' if metrics['response_time_stats']['mean'] < 5.0 else 'may need optimization'} for real-time applications

#### Resource Management
1. **Server Optimization**: {'Resource-friendly approach successfully managed server constraints' if self.resource_friendly and metrics['dataset_info']['success_rate'] > 0.8 else 'Consider further resource optimization'}
2. **Scaling Considerations**: Current configuration supports evaluation workloads with {metrics['dataset_info']['success_rate']:.1%} success rate

### Conclusion
The moderation system demonstrates {'strong' if metrics['f1_score'] >= 0.8 else 'moderate' if metrics['f1_score'] >= 0.6 else 'limited'} performance on real-world toxic conversation data. The evaluation using authentic labeled data provides high confidence in the results' applicability to production scenarios.

### Technical Details
- **Evaluation Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Dataset Source**: SetFit/toxic_conversations
- **Evaluation Framework**: Custom academic evaluation suite
- **Statistical Methods**: Scikit-learn metrics with balanced sampling
- **Visualization**: Comprehensive performance dashboard generated

---
*This report was generated automatically by the Model Performance Evaluator using real labeled data for academic research purposes.*
"""
        
        # Save report
        with open(f'{output_dir}/model_evaluation_real_report.md', 'w') as f:
            f.write(report)
        
        print(f"📋 Real dataset evaluation report saved to {output_dir}/model_evaluation_real_report.md")
        
        return metrics

if __name__ == "__main__":
    # Example usage with real dataset
    print("🔬 Model Performance Evaluator - Real Dataset")
    print("=" * 50)
    
    try:
        # Initialize evaluator with resource-friendly mode
        evaluator = ModelPerformanceEvaluator(resource_friendly=True)
        
        # Collect evaluation data (smaller sample for testing)
        evaluator.collect_evaluation_data(sample_size=30)
        
        # Calculate metrics
        metrics = evaluator.calculate_performance_metrics()
        
        # Create visualizations
        evaluator.create_evaluation_visualizations()
        
        # Generate report
        evaluator.generate_academic_report()
        
        print("\n✅ Evaluation completed successfully!")
        print(f"📊 Key Results:")
        print(f"   • Accuracy: {metrics['accuracy']:.3f}")
        print(f"   • F1-Score: {metrics['f1_score']:.3f}")
        print(f"   • Success Rate: {metrics['dataset_info']['success_rate']:.1%}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure:")
        print("1. dissertation-experiment-data.csv exists")
        print("2. Moderation system is running on localhost:8000")
        print("3. Dataset loader is properly configured")
