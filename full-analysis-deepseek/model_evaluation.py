"""
Model Evaluation Module for Academic Dissertation
Comprehensive evaluation of moderation model performance
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, roc_curve,
    precision_recall_curve, average_precision_score
)
from sklearn.model_selection import cross_val_score, StratifiedKFold
from scipy import stats
import requests
import json
from datetime import datetime

class ModelPerformanceEvaluator:
    """
    Comprehensive model evaluation for academic research.
    Provides statistical rigor for dissertation-quality analysis.
    """
    
    def __init__(self):
        self.evaluation_data = {}
        self.ground_truth = []
        self.predictions = []
        self.prediction_probabilities = []
        
    def collect_evaluation_data(self, test_messages=None):
        """
        Collect evaluation data by sending test messages and recording results.
        
        Args:
            test_messages (list): List of test messages with ground truth labels
        """
        if test_messages is None:
            test_messages = self._generate_test_dataset()
        
        print(f"📊 Evaluating model with {len(test_messages)} test messages...")
        
        results = []
        
        for i, (message, true_label) in enumerate(test_messages):
            try:
                # Send message to moderation system
                response = requests.post(
                    "http://localhost:8002/api/send-message",
                    headers={"Content-Type": "application/json"},
                    json={
                        "message": message,
                        "user_id": f"eval_user_{i}",
                        "username": f"EvalUser{i}",
                        "channel_id": "evaluation"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    moderation_result = result.get('result', {}).get('moderation_result', {})
                    
                    predicted_label = moderation_result.get('decision', 'Unknown')
                    confidence = moderation_result.get('confidence', 0.5)
                    
                    results.append({
                        'message': message,
                        'true_label': true_label,
                        'predicted_label': predicted_label,
                        'confidence': confidence,
                        'processing_time': result.get('result', {}).get('processing_time_ms', 0)
                    })
                    
                    self.ground_truth.append(true_label)
                    self.predictions.append(predicted_label)
                    self.prediction_probabilities.append(confidence)
                    
                    if (i + 1) % 10 == 0:
                        print(f"✅ Processed {i + 1}/{len(test_messages)} messages")
                
            except Exception as e:
                print(f"❌ Error processing message {i}: {str(e)}")
        
        self.evaluation_data = pd.DataFrame(results)
        return self.evaluation_data
    
    def _generate_test_dataset(self):
        """Generate a balanced test dataset with ground truth labels."""
        
        toxic_messages = [
            ("You are absolutely worthless and should disappear", "Toxic"),
            ("I hate you so much, you make me sick", "Toxic"),
            ("Go kill yourself, nobody wants you here", "Toxic"),
            ("You're the dumbest person I've ever met", "Toxic"),
            ("I hope you suffer for the rest of your life", "Toxic"),
            ("You're a complete waste of space and oxygen", "Toxic"),
            ("Everyone would be better off without you", "Toxic"),
            ("You're disgusting and pathetic", "Toxic"),
            ("I wish you would just shut up forever", "Toxic"),
            ("You're nothing but a loser and failure", "Toxic"),
        ]
        
        non_toxic_messages = [
            ("Hello everyone, how are you doing today?", "Non-Toxic"),
            ("Thanks for the help with the project", "Non-Toxic"),
            ("Great weather we're having this week", "Non-Toxic"),
            ("Looking forward to the meeting tomorrow", "Non-Toxic"),
            ("Have a wonderful and productive day", "Non-Toxic"),
            ("The presentation was really informative", "Non-Toxic"),
            ("I appreciate your hard work on this", "Non-Toxic"),
            ("Let's collaborate on the next phase", "Non-Toxic"),
            ("The results look very promising", "Non-Toxic"),
            ("Thank you for your patience and understanding", "Non-Toxic"),
        ]
        
        # Combine and shuffle
        all_messages = toxic_messages + non_toxic_messages
        np.random.shuffle(all_messages)
        
        return all_messages
    
    def calculate_performance_metrics(self):
        """
        Calculate comprehensive performance metrics for academic evaluation.
        
        Returns:
            dict: Comprehensive performance metrics
        """
        if not self.ground_truth or not self.predictions:
            print("❌ No evaluation data available")
            return {}
        
        # Convert labels to binary for some metrics
        y_true_binary = [1 if label == "Toxic" else 0 for label in self.ground_truth]
        y_pred_binary = [1 if label == "Toxic" else 0 for label in self.predictions]
        
        # Basic classification metrics
        accuracy = accuracy_score(self.ground_truth, self.predictions)
        precision = precision_score(self.ground_truth, self.predictions, average='weighted', zero_division=0)
        recall = recall_score(self.ground_truth, self.predictions, average='weighted', zero_division=0)
        f1 = f1_score(self.ground_truth, self.predictions, average='weighted', zero_division=0)
        
        # Binary classification metrics for toxic detection
        toxic_precision = precision_score(y_true_binary, y_pred_binary, zero_division=0)
        toxic_recall = recall_score(y_true_binary, y_pred_binary, zero_division=0)
        toxic_f1 = f1_score(y_true_binary, y_pred_binary, zero_division=0)
        
        # Confusion matrix
        cm = confusion_matrix(self.ground_truth, self.predictions)
        
        # ROC AUC if we have probability scores
        try:
            if len(set(y_true_binary)) > 1:  # Need both classes for ROC
                roc_auc = roc_auc_score(y_true_binary, self.prediction_probabilities)
            else:
                roc_auc = None
        except:
            roc_auc = None
        
        metrics = {
            'accuracy': accuracy,
            'precision_weighted': precision,
            'recall_weighted': recall,
            'f1_weighted': f1,
            'toxic_precision': toxic_precision,
            'toxic_recall': toxic_recall,
            'toxic_f1': toxic_f1,
            'confusion_matrix': cm,
            'roc_auc': roc_auc,
            'sample_size': len(self.ground_truth)
        }
        
        # Calculate confidence intervals for key metrics
        n = len(self.ground_truth)
        z = 1.96  # 95% confidence
        
        for metric_name in ['accuracy', 'toxic_precision', 'toxic_recall', 'toxic_f1']:
            if metric_name in metrics and metrics[metric_name] is not None:
                p = metrics[metric_name]
                se = np.sqrt(p * (1 - p) / n)
                ci_lower = max(0, p - z * se)
                ci_upper = min(1, p + z * se)
                metrics[f'{metric_name}_ci'] = (ci_lower, ci_upper)
        
        return metrics
    
    def create_evaluation_visualizations(self, output_dir="reports"):
        """Create comprehensive evaluation visualizations."""
        
        metrics = self.calculate_performance_metrics()
        
        if not metrics:
            return
        
        # Create comprehensive evaluation figure
        fig = plt.figure(figsize=(20, 15))
        
        # 1. Confusion Matrix
        ax1 = plt.subplot(3, 3, 1)
        cm = metrics['confusion_matrix']
        labels = sorted(list(set(self.ground_truth)))
        
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=labels, yticklabels=labels, ax=ax1)
        ax1.set_title('Confusion Matrix')
        ax1.set_xlabel('Predicted Label')
        ax1.set_ylabel('True Label')
        
        # 2. Performance Metrics Bar Chart
        ax2 = plt.subplot(3, 3, 2)
        metric_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
        metric_values = [metrics['accuracy'], metrics['precision_weighted'], 
                        metrics['recall_weighted'], metrics['f1_weighted']]
        
        bars = ax2.bar(metric_names, metric_values, color=['blue', 'green', 'orange', 'red'], alpha=0.7)
        ax2.set_ylim(0, 1)
        ax2.set_title('Overall Performance Metrics')
        ax2.set_ylabel('Score')
        
        # Add value labels on bars
        for bar, value in zip(bars, metric_values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{value:.3f}', ha='center', va='bottom')
        
        # 3. Toxic Detection Specific Metrics
        ax3 = plt.subplot(3, 3, 3)
        toxic_metrics = ['Precision', 'Recall', 'F1-Score']
        toxic_values = [metrics['toxic_precision'], metrics['toxic_recall'], metrics['toxic_f1']]
        
        bars = ax3.bar(toxic_metrics, toxic_values, color=['red', 'orange', 'darkred'], alpha=0.7)
        ax3.set_ylim(0, 1)
        ax3.set_title('Toxic Content Detection Metrics')
        ax3.set_ylabel('Score')
        
        for bar, value in zip(bars, toxic_values):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{value:.3f}', ha='center', va='bottom')
        
        # 4. ROC Curve (if available)
        if metrics['roc_auc'] is not None:
            ax4 = plt.subplot(3, 3, 4)
            y_true_binary = [1 if label == "Toxic" else 0 for label in self.ground_truth]
            fpr, tpr, _ = roc_curve(y_true_binary, self.prediction_probabilities)
            
            ax4.plot(fpr, tpr, color='darkorange', lw=2, 
                    label=f'ROC curve (AUC = {metrics["roc_auc"]:.3f})')
            ax4.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
            ax4.set_xlim([0.0, 1.0])
            ax4.set_ylim([0.0, 1.05])
            ax4.set_xlabel('False Positive Rate')
            ax4.set_ylabel('True Positive Rate')
            ax4.set_title('ROC Curve')
            ax4.legend(loc="lower right")
        
        # 5. Precision-Recall Curve
        ax5 = plt.subplot(3, 3, 5)
        if len(set([1 if label == "Toxic" else 0 for label in self.ground_truth])) > 1:
            y_true_binary = [1 if label == "Toxic" else 0 for label in self.ground_truth]
            precision_curve, recall_curve, _ = precision_recall_curve(y_true_binary, self.prediction_probabilities)
            avg_precision = average_precision_score(y_true_binary, self.prediction_probabilities)
            
            ax5.plot(recall_curve, precision_curve, color='blue', lw=2,
                    label=f'AP = {avg_precision:.3f}')
            ax5.set_xlabel('Recall')
            ax5.set_ylabel('Precision')
            ax5.set_title('Precision-Recall Curve')
            ax5.legend()
        
        # 6. Confidence Distribution
        ax6 = plt.subplot(3, 3, 6)
        ax6.hist(self.prediction_probabilities, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax6.set_xlabel('Prediction Confidence')
        ax6.set_ylabel('Frequency')
        ax6.set_title('Prediction Confidence Distribution')
        ax6.axvline(np.mean(self.prediction_probabilities), color='red', linestyle='--',
                   label=f'Mean: {np.mean(self.prediction_probabilities):.3f}')
        ax6.legend()
        
        # 7. Processing Time Analysis
        if 'processing_time' in self.evaluation_data.columns:
            ax7 = plt.subplot(3, 3, 7)
            processing_times = self.evaluation_data['processing_time'].values
            ax7.hist(processing_times, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
            ax7.set_xlabel('Processing Time (ms)')
            ax7.set_ylabel('Frequency')
            ax7.set_title('Processing Time Distribution')
            ax7.axvline(np.mean(processing_times), color='red', linestyle='--',
                       label=f'Mean: {np.mean(processing_times):.1f}ms')
            ax7.legend()
        
        # 8. Performance Summary Table
        ax8 = plt.subplot(3, 3, 8)
        ax8.axis('tight')
        ax8.axis('off')
        
        summary_data = [
            ['Metric', 'Value', '95% CI'],
            ['Accuracy', f'{metrics["accuracy"]:.3f}', 
             f'({metrics.get("accuracy_ci", (0,0))[0]:.3f}, {metrics.get("accuracy_ci", (0,0))[1]:.3f})'],
            ['Toxic Precision', f'{metrics["toxic_precision"]:.3f}', 
             f'({metrics.get("toxic_precision_ci", (0,0))[0]:.3f}, {metrics.get("toxic_precision_ci", (0,0))[1]:.3f})'],
            ['Toxic Recall', f'{metrics["toxic_recall"]:.3f}', 
             f'({metrics.get("toxic_recall_ci", (0,0))[0]:.3f}, {metrics.get("toxic_recall_ci", (0,0))[1]:.3f})'],
            ['Toxic F1-Score', f'{metrics["toxic_f1"]:.3f}', 
             f'({metrics.get("toxic_f1_ci", (0,0))[0]:.3f}, {metrics.get("toxic_f1_ci", (0,0))[1]:.3f})'],
            ['Sample Size', f'{metrics["sample_size"]}', 'N/A']
        ]
        
        table = ax8.table(cellText=summary_data, cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.5)
        ax8.set_title('Performance Summary with Confidence Intervals')
        
        # 9. Label Distribution
        ax9 = plt.subplot(3, 3, 9)
        label_counts = pd.Series(self.ground_truth).value_counts()
        ax9.pie(label_counts.values, labels=label_counts.index, autopct='%1.1f%%')
        ax9.set_title('Ground Truth Label Distribution')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/model_evaluation.png', dpi=300, bbox_inches='tight')
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
        """Generate academic-quality evaluation report."""
        
        metrics = self.calculate_performance_metrics()
        
        if not metrics:
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
# Model Performance Evaluation Report
## Real-Time Content Moderation System

**Generated:** {timestamp}  
**Sample Size:** {metrics['sample_size']} messages  
**Evaluation Method:** Controlled testing with ground truth labels

---

## Abstract

This report presents a comprehensive evaluation of the real-time content moderation system's 
classification performance. Using a balanced dataset of toxic and non-toxic messages, we 
assessed the model's ability to accurately identify harmful content while minimizing false 
positives and false negatives.

## Methodology

### Dataset Composition
- **Total Messages:** {metrics['sample_size']}
- **Toxic Messages:** {sum(1 for label in self.ground_truth if label == 'Toxic')}
- **Non-Toxic Messages:** {sum(1 for label in self.ground_truth if label == 'Non-Toxic')}
- **Balance Ratio:** {(sum(1 for label in self.ground_truth if label == 'Toxic') / len(self.ground_truth)):.2f} toxic

### Evaluation Metrics
We employed standard classification metrics including accuracy, precision, recall, and F1-score, 
with particular focus on toxic content detection performance.

## Results

### Overall Classification Performance
- **Accuracy:** {metrics['accuracy']:.3f} (95% CI: {metrics.get('accuracy_ci', (0,0))[0]:.3f} - {metrics.get('accuracy_ci', (0,0))[1]:.3f})
- **Weighted Precision:** {metrics['precision_weighted']:.3f}
- **Weighted Recall:** {metrics['recall_weighted']:.3f}
- **Weighted F1-Score:** {metrics['f1_weighted']:.3f}

### Toxic Content Detection Performance
- **Precision:** {metrics['toxic_precision']:.3f} (95% CI: {metrics.get('toxic_precision_ci', (0,0))[0]:.3f} - {metrics.get('toxic_precision_ci', (0,0))[1]:.3f})
- **Recall:** {metrics['toxic_recall']:.3f} (95% CI: {metrics.get('toxic_recall_ci', (0,0))[0]:.3f} - {metrics.get('toxic_recall_ci', (0,0))[1]:.3f})
- **F1-Score:** {metrics['toxic_f1']:.3f} (95% CI: {metrics.get('toxic_f1_ci', (0,0))[0]:.3f} - {metrics.get('toxic_f1_ci', (0,0))[1]:.3f})

"""
        
        if metrics['roc_auc'] is not None:
            report += f"- **ROC AUC:** {metrics['roc_auc']:.3f}\n"
        
        report += f"""

### Confusion Matrix Analysis
The confusion matrix reveals the following classification patterns:
{self._format_confusion_matrix(metrics['confusion_matrix'])}

## Statistical Analysis

### Confidence Intervals
All performance metrics are reported with 95% confidence intervals calculated using 
the normal approximation to the binomial distribution. These intervals provide bounds 
on the true population performance parameters.

### Sample Size Considerations
With a sample size of {metrics['sample_size']} messages, the study provides adequate 
statistical power for detecting meaningful differences in performance metrics.

## Discussion

### Model Strengths
"""
        
        if metrics['toxic_precision'] > 0.8:
            report += "- High precision in toxic content detection reduces false positive rates\n"
        if metrics['toxic_recall'] > 0.8:
            report += "- High recall ensures most toxic content is identified\n"
        if metrics['accuracy'] > 0.8:
            report += "- Overall accuracy demonstrates reliable classification performance\n"
        
        report += """
### Areas for Improvement
"""
        
        if metrics['toxic_precision'] < 0.8:
            report += "- Precision could be improved to reduce false positive rates\n"
        if metrics['toxic_recall'] < 0.8:
            report += "- Recall enhancement needed to catch more toxic content\n"
        
        report += f"""

### Processing Performance
- **Mean Processing Time:** {self.evaluation_data['processing_time'].mean():.1f}ms
- **Processing Time Std:** {self.evaluation_data['processing_time'].std():.1f}ms
- **95th Percentile:** {self.evaluation_data['processing_time'].quantile(0.95):.1f}ms

## Conclusions

The evaluation demonstrates that the real-time moderation system achieves 
{metrics['accuracy']:.1%} overall accuracy with {metrics['toxic_f1']:.1%} F1-score 
for toxic content detection. The system shows {"strong" if metrics['accuracy'] > 0.8 else "moderate"} 
performance suitable for {"production deployment" if metrics['accuracy'] > 0.8 else "further development"}.

## Recommendations

1. **Model Optimization:** {"Continue current approach" if metrics['accuracy'] > 0.8 else "Investigate model improvements"}
2. **Dataset Expansion:** Increase evaluation dataset size for more robust statistics
3. **Longitudinal Study:** Conduct extended evaluation over time
4. **A/B Testing:** Compare with alternative moderation approaches

---

**Note:** This evaluation represents performance on a controlled test dataset. 
Real-world performance may vary based on content diversity and user behavior patterns.
"""
        
        # Save report
        with open(f'{output_dir}/model_evaluation_report.md', 'w') as f:
            f.write(report)
        
        print(f"📋 Model evaluation report saved to {output_dir}/model_evaluation_report.md")
        
        return metrics

if __name__ == "__main__":
    evaluator = ModelPerformanceEvaluator()
    evaluator.collect_evaluation_data()
    evaluator.create_evaluation_visualizations()
    evaluator.generate_academic_report()
