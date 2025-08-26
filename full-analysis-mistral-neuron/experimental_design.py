"""
Experimental Design Module for Academic Research
Provides rigorous experimental frameworks for dissertation research
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.model_selection import train_test_split
import requests
import json
import time
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor

class ExperimentalDesign:
    """
    Comprehensive experimental design framework for academic research.
    Supports A/B testing, controlled experiments, and statistical analysis.
    """
    
    def __init__(self):
        self.experiments = {}
        self.results = {}
        
    def design_controlled_experiment(self, experiment_name, test_conditions):
        """
        Design a controlled experiment with multiple conditions.
        
        Args:
            experiment_name (str): Name of the experiment
            test_conditions (dict): Dictionary of conditions and their parameters
        """
        experiment = {
            'name': experiment_name,
            'conditions': test_conditions,
            'start_time': None,
            'end_time': None,
            'results': {},
            'statistical_analysis': {}
        }
        
        self.experiments[experiment_name] = experiment
        return experiment
    
    def generate_experimental_dataset(self, size=30, toxicity_rate=0.3):
        """
        Generate a comprehensive experimental dataset with known ground truth.
        
        Args:
            size (int): Total number of messages to generate
            toxicity_rate (float): Proportion of toxic messages
            
        Returns:
            list: List of (message, label, metadata) tuples
        """
        print(f"🧪 Generating experimental dataset: {size} messages, {toxicity_rate:.1%} toxic")
        
        # Toxic message templates with varying severity
        toxic_templates = {
            'high_severity': [
                "You are absolutely worthless and should {action}",
                "I hate you so much, you {negative_trait}",
                "Go {harmful_action}, nobody wants you here",
                "You're the {superlative} {negative_noun} I've ever met",
                "I hope you {negative_outcome} for the rest of your life"
            ],
            'medium_severity': [
                "You're really {mild_negative} and {mild_negative2}",
                "I don't like you because you're {negative_trait}",
                "You always {annoying_behavior} and it's irritating",
                "Stop being such a {mild_insult}",
                "You're not very {positive_trait} at all"
            ],
            'low_severity': [
                "I disagree with your {opinion_topic}",
                "That's not a good {thing}",
                "I don't think you're right about {topic}",
                "Your {work_output} could be better",
                "I'm not impressed with {performance_area}"
            ]
        }
        
        # Non-toxic message templates
        non_toxic_templates = [
            "Hello everyone, how are you doing {time_period}?",
            "Thanks for the help with {task}",
            "Great {positive_thing} we're having!",
            "Looking forward to {future_event}",
            "Have a wonderful {time_period}",
            "The {thing} was really {positive_adjective}",
            "I appreciate your {positive_action}",
            "Let's {collaborative_action} on {project}",
            "The results look very {positive_outcome}",
            "Thank you for your {virtue} and {virtue2}"
        ]
        
        # Word banks for template filling
        word_banks = {
            'action': ['disappear', 'leave', 'quit', 'stop'],
            'negative_trait': ['annoying', 'stupid', 'useless', 'pathetic'],
            'harmful_action': ['away', 'home', 'somewhere else'],
            'superlative': ['dumbest', 'worst', 'most annoying'],
            'negative_noun': ['person', 'individual', 'human'],
            'negative_outcome': ['struggle', 'fail', 'regret'],
            'mild_negative': ['annoying', 'frustrating', 'difficult'],
            'mild_negative2': ['stubborn', 'unreasonable', 'inconsiderate'],
            'annoying_behavior': ['interrupt', 'complain', 'argue'],
            'mild_insult': ['know-it-all', 'show-off', 'complainer'],
            'positive_trait': ['smart', 'helpful', 'kind'],
            'time_period': ['today', 'this week', 'lately'],
            'task': ['the project', 'this issue', 'the problem'],
            'positive_thing': ['weather', 'progress', 'news'],
            'future_event': ['the meeting', 'tomorrow', 'next week'],
            'thing': ['presentation', 'report', 'discussion'],
            'positive_adjective': ['informative', 'helpful', 'interesting'],
            'positive_action': ['hard work', 'dedication', 'support'],
            'collaborative_action': ['work together', 'collaborate', 'team up'],
            'project': ['this task', 'the next phase', 'our goal'],
            'positive_outcome': ['promising', 'encouraging', 'positive'],
            'virtue': ['patience', 'understanding', 'kindness'],
            'virtue2': ['support', 'help', 'guidance']
        }
        
        dataset = []
        toxic_count = int(size * toxicity_rate)
        non_toxic_count = size - toxic_count
        
        # Generate toxic messages
        for i in range(toxic_count):
            severity = np.random.choice(['high_severity', 'medium_severity', 'low_severity'], 
                                      p=[0.2, 0.5, 0.3])
            template = np.random.choice(toxic_templates[severity])
            
            # Fill template with random words
            message = template
            for placeholder, words in word_banks.items():
                if f'{{{placeholder}}}' in message:
                    message = message.replace(f'{{{placeholder}}}', np.random.choice(words))
            
            dataset.append((
                message,
                'Toxic',
                {
                    'severity': severity,
                    'message_id': f'toxic_{i}',
                    'generated': True,
                    'template_used': template
                }
            ))
        
        # Generate non-toxic messages
        for i in range(non_toxic_count):
            template = np.random.choice(non_toxic_templates)
            
            # Fill template with random words
            message = template
            for placeholder, words in word_banks.items():
                if f'{{{placeholder}}}' in message:
                    message = message.replace(f'{{{placeholder}}}', np.random.choice(words))
            
            dataset.append((
                message,
                'Non-Toxic',
                {
                    'message_id': f'non_toxic_{i}',
                    'generated': True,
                    'template_used': template
                }
            ))
        
        # Shuffle dataset
        np.random.shuffle(dataset)
        
        print(f"✅ Generated {len(dataset)} messages ({toxic_count} toxic, {non_toxic_count} non-toxic)")
        return dataset
    
    def run_performance_experiment(self, experiment_name, dataset, batch_sizes=[1, 5, 10, 20]):
        """
        Run performance experiment with different batch sizes.
        
        Args:
            experiment_name (str): Name of the experiment
            dataset (list): Test dataset
            batch_sizes (list): Different batch sizes to test
        """
        print(f"🚀 Running performance experiment: {experiment_name}")
        
        experiment = self.experiments.get(experiment_name, {})
        experiment['start_time'] = datetime.now()
        
        results = {}
        
        for batch_size in batch_sizes:
            print(f"📊 Testing batch size: {batch_size}")
            
            batch_results = {
                'batch_size': batch_size,
                'processing_times': [],
                'response_times': [],
                'success_rate': 0,
                'error_count': 0,
                'total_requests': 0
            }
            
            # Process messages in batches
            batches = [dataset[i:i+batch_size] for i in range(0, len(dataset), batch_size)]
            
            for batch_idx, batch in enumerate(batches[:10]):  # Limit to 10 batches for testing
                batch_start = time.time()
                
                # Process batch concurrently
                with ThreadPoolExecutor(max_workers=batch_size) as executor:
                    futures = []
                    
                    for message, label, metadata in batch:
                        future = executor.submit(self._send_message_for_experiment, 
                                               message, label, metadata, batch_idx)
                        futures.append(future)
                    
                    # Collect results
                    for future in futures:
                        try:
                            result = future.result(timeout=30)
                            if result:
                                batch_results['processing_times'].append(result['processing_time'])
                                batch_results['response_times'].append(result['response_time'])
                                batch_results['total_requests'] += 1
                                if result['success']:
                                    batch_results['success_rate'] += 1
                                else:
                                    batch_results['error_count'] += 1
                        except Exception as e:
                            batch_results['error_count'] += 1
                            batch_results['total_requests'] += 1
                
                batch_end = time.time()
                print(f"  Batch {batch_idx + 1} completed in {batch_end - batch_start:.2f}s")
            
            # Calculate final metrics
            if batch_results['total_requests'] > 0:
                batch_results['success_rate'] = batch_results['success_rate'] / batch_results['total_requests']
                batch_results['avg_processing_time'] = np.mean(batch_results['processing_times'])
                batch_results['avg_response_time'] = np.mean(batch_results['response_times'])
                batch_results['throughput'] = batch_results['total_requests'] / sum(batch_results['response_times']) * 1000
            
            results[batch_size] = batch_results
        
        experiment['end_time'] = datetime.now()
        experiment['results'] = results
        self.experiments[experiment_name] = experiment
        
        return results
    
    def _send_message_for_experiment(self, message, label, metadata, batch_idx):
        """Send a single message for experimental evaluation."""
        
        start_time = time.time()
        
        try:
            response = requests.post(
                "http://localhost:8002/api/send-message",
                headers={"Content-Type": "application/json"},
                json={
                    "message": message,
                    "user_id": f"exp_user_{metadata['message_id']}",
                    "username": f"ExpUser{batch_idx}",
                    "channel_id": "experiment"
                },
                timeout=30
            )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200:
                result = response.json()
                processing_time = result.get('result', {}).get('processing_time_ms', 0)
                
                return {
                    'success': True,
                    'processing_time': processing_time,
                    'response_time': response_time,
                    'prediction': result.get('result', {}).get('moderation_result', {}).get('decision'),
                    'true_label': label
                }
            else:
                return {
                    'success': False,
                    'processing_time': 0,
                    'response_time': response_time,
                    'prediction': None,
                    'true_label': label
                }
                
        except Exception as e:
            end_time = time.time()
            return {
                'success': False,
                'processing_time': 0,
                'response_time': (end_time - start_time) * 1000,
                'prediction': None,
                'true_label': label,
                'error': str(e)
            }
    
    def analyze_experiment_results(self, experiment_name):
        """
        Perform statistical analysis of experiment results.
        
        Args:
            experiment_name (str): Name of the experiment to analyze
            
        Returns:
            dict: Statistical analysis results
        """
        if experiment_name not in self.experiments:
            print(f"❌ Experiment '{experiment_name}' not found")
            return {}
        
        experiment = self.experiments[experiment_name]
        results = experiment.get('results', {})
        
        if not results:
            print(f"❌ No results found for experiment '{experiment_name}'")
            return {}
        
        print(f"📊 Analyzing experiment results: {experiment_name}")
        
        analysis = {
            'experiment_name': experiment_name,
            'batch_sizes': list(results.keys()),
            'performance_comparison': {},
            'statistical_tests': {},
            'recommendations': []
        }
        
        # Extract metrics for analysis
        batch_sizes = []
        avg_processing_times = []
        avg_response_times = []
        success_rates = []
        throughputs = []
        
        for batch_size, batch_results in results.items():
            batch_sizes.append(batch_size)
            avg_processing_times.append(batch_results.get('avg_processing_time', 0))
            avg_response_times.append(batch_results.get('avg_response_time', 0))
            success_rates.append(batch_results.get('success_rate', 0))
            throughputs.append(batch_results.get('throughput', 0))
        
        # Performance comparison
        analysis['performance_comparison'] = {
            'batch_sizes': batch_sizes,
            'processing_times': {
                'values': avg_processing_times,
                'best_batch_size': batch_sizes[np.argmin(avg_processing_times)],
                'worst_batch_size': batch_sizes[np.argmax(avg_processing_times)]
            },
            'response_times': {
                'values': avg_response_times,
                'best_batch_size': batch_sizes[np.argmin(avg_response_times)],
                'worst_batch_size': batch_sizes[np.argmax(avg_response_times)]
            },
            'success_rates': {
                'values': success_rates,
                'best_batch_size': batch_sizes[np.argmax(success_rates)],
                'worst_batch_size': batch_sizes[np.argmin(success_rates)]
            },
            'throughputs': {
                'values': throughputs,
                'best_batch_size': batch_sizes[np.argmax(throughputs)],
                'worst_batch_size': batch_sizes[np.argmin(throughputs)]
            }
        }
        
        # Statistical tests
        if len(batch_sizes) > 2:
            # ANOVA for processing times
            processing_time_groups = []
            for batch_size, batch_results in results.items():
                processing_time_groups.append(batch_results.get('processing_times', []))
            
            if all(len(group) > 0 for group in processing_time_groups):
                f_stat, p_value = stats.f_oneway(*processing_time_groups)
                analysis['statistical_tests']['processing_time_anova'] = {
                    'f_statistic': f_stat,
                    'p_value': p_value,
                    'significant': p_value < 0.05
                }
        
        # Correlation analysis
        if len(batch_sizes) > 2:
            # Correlation between batch size and performance metrics
            correlations = {
                'batch_size_vs_processing_time': stats.pearsonr(batch_sizes, avg_processing_times),
                'batch_size_vs_response_time': stats.pearsonr(batch_sizes, avg_response_times),
                'batch_size_vs_success_rate': stats.pearsonr(batch_sizes, success_rates),
                'batch_size_vs_throughput': stats.pearsonr(batch_sizes, throughputs)
            }
            
            analysis['statistical_tests']['correlations'] = {}
            for metric, (corr, p_val) in correlations.items():
                analysis['statistical_tests']['correlations'][metric] = {
                    'correlation': corr,
                    'p_value': p_val,
                    'significant': p_val < 0.05
                }
        
        # Generate recommendations
        best_overall = batch_sizes[np.argmax(throughputs)]
        analysis['recommendations'] = [
            f"Optimal batch size for throughput: {best_overall}",
            f"Lowest processing time with batch size: {analysis['performance_comparison']['processing_times']['best_batch_size']}",
            f"Highest success rate with batch size: {analysis['performance_comparison']['success_rates']['best_batch_size']}"
        ]
        
        experiment['statistical_analysis'] = analysis
        return analysis
    
    def create_experiment_visualizations(self, experiment_name, output_dir="analysis/reports"):
        """Create comprehensive visualizations for experiment results."""
        
        if experiment_name not in self.experiments:
            return
        
        experiment = self.experiments[experiment_name]
        results = experiment.get('results', {})
        analysis = experiment.get('statistical_analysis', {})
        
        if not results:
            return
        
        # Create comprehensive experiment visualization
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'Experimental Results: {experiment_name}', fontsize=16, fontweight='bold')
        
        batch_sizes = list(results.keys())
        
        # 1. Processing Time vs Batch Size
        processing_times = [results[bs].get('avg_processing_time', 0) for bs in batch_sizes]
        ax1.plot(batch_sizes, processing_times, 'o-', linewidth=2, markersize=8, color='blue')
        ax1.set_xlabel('Batch Size')
        ax1.set_ylabel('Average Processing Time (ms)')
        ax1.set_title('Processing Time vs Batch Size')
        ax1.grid(True, alpha=0.3)
        
        # 2. Success Rate vs Batch Size
        success_rates = [results[bs].get('success_rate', 0) for bs in batch_sizes]
        ax2.plot(batch_sizes, success_rates, 'o-', linewidth=2, markersize=8, color='green')
        ax2.set_xlabel('Batch Size')
        ax2.set_ylabel('Success Rate')
        ax2.set_title('Success Rate vs Batch Size')
        ax2.set_ylim(0, 1)
        ax2.grid(True, alpha=0.3)
        
        # 3. Throughput vs Batch Size
        throughputs = [results[bs].get('throughput', 0) for bs in batch_sizes]
        ax3.plot(batch_sizes, throughputs, 'o-', linewidth=2, markersize=8, color='red')
        ax3.set_xlabel('Batch Size')
        ax3.set_ylabel('Throughput (requests/second)')
        ax3.set_title('Throughput vs Batch Size')
        ax3.grid(True, alpha=0.3)
        
        # 4. Performance Summary Table
        ax4.axis('tight')
        ax4.axis('off')
        
        summary_data = [['Batch Size', 'Proc. Time (ms)', 'Success Rate', 'Throughput']]
        for bs in batch_sizes:
            summary_data.append([
                str(bs),
                f"{results[bs].get('avg_processing_time', 0):.1f}",
                f"{results[bs].get('success_rate', 0):.3f}",
                f"{results[bs].get('throughput', 0):.2f}"
            ])
        
        table = ax4.table(cellText=summary_data, cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        ax4.set_title('Performance Summary')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/experiment_{experiment_name.replace(" ", "_")}.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Experiment visualization saved for {experiment_name}")

if __name__ == "__main__":
    # Example usage
    designer = ExperimentalDesign()
    
    # Design experiment
    experiment = designer.design_controlled_experiment(
        "Batch_Size_Performance",
        {"batch_sizes": [1, 5, 10, 20]}
    )
    
    # Generate test dataset
    dataset = designer.generate_experimental_dataset(size=30, toxicity_rate=0.3)
    
    # Run experiment
    results = designer.run_performance_experiment("Batch_Size_Performance", dataset)
    
    # Analyze results
    analysis = designer.analyze_experiment_results("Batch_Size_Performance")
    
    # Create visualizations
    designer.create_experiment_visualizations("Batch_Size_Performance")
