#!/usr/bin/env python3
"""
Experimental Design for Real-Time Moderation System
==================================================

This module conducts systematic experiments using real labeled data from the 
SetFit/toxic_conversations dataset with resource-friendly approaches for 
constrained server environments.

Author: Academic Research
Date: 2025
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import json
import time
from datetime import datetime
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')

# Import our dataset loader
from dataset_loader import DissertationDatasetLoader

class ExperimentalDesign:
    """
    Systematic experimental design for moderation system evaluation using real data.
    Implements resource-friendly testing strategies for constrained environments.
    """
    
    def __init__(self, csv_path="dissertation-experiment-data.csv", resource_friendly=True):
        """
        Initialize experimental design with real dataset.
        
        Args:
            csv_path (str): Path to the dissertation dataset CSV file
            resource_friendly (bool): Enable resource-friendly experiment mode
        """
        self.experiments = {}
        self.results = {}
        
        # Ultra-conservative configuration for overloaded Mistral server
        self.resource_friendly = resource_friendly
        self.request_delay = 15.0 if resource_friendly else 3.0     # Much longer delay between requests
        self.timeout = 120.0 if resource_friendly else 60.0        # Extended timeout for slow generation
        self.max_retries = 2 if resource_friendly else 5           # Fewer retries to avoid pile-up
        self.batch_delay = 60.0 if resource_friendly else 10.0     # Long delay between batches
        self.max_batch_size = 3 if resource_friendly else 10       # Very small batches
        
        # Load the real dataset
        self.dataset_loader = DissertationDatasetLoader(csv_path)
        print(f"🧪 Initialized Experimental Design ({'Resource-Friendly' if resource_friendly else 'Standard'} mode)")
        
    def create_experiment(self, name: str, description: str, parameters: Dict):
        """
        Create a new experiment configuration.
        
        Args:
            name (str): Experiment name
            description (str): Experiment description
            parameters (Dict): Experiment parameters
        """
        experiment = {
            'name': name,
            'description': description,
            'parameters': parameters,
            'created_at': datetime.now(),
            'status': 'created'
        }
        
        self.experiments[name] = experiment
        print(f"🔬 Created experiment: {name}")
        return experiment
    
    def get_experimental_dataset(self, size=30, strategy='balanced', random_state=42):
        """
        Get experimental dataset from real data using specified strategy.
        
        Args:
            size (int): Number of samples to use
            strategy (str): Sampling strategy ('balanced', 'stratified', 'random')
            random_state (int): Random seed for reproducibility
            
        Returns:
            List[Tuple[str, str]]: List of (message, label) tuples
        """
        print(f"🧪 Generating experimental dataset: {size} messages using '{strategy}' strategy")
        
        if strategy == 'balanced':
            dataset = self.dataset_loader.get_balanced_sample(
                n_samples=size, 
                random_state=random_state
            )
        elif strategy == 'stratified':
            dataset = self.dataset_loader.get_stratified_sample(
                n_samples=size, 
                maintain_ratio=True,
                random_state=random_state
            )
        else:  # random
            # Get random sample maintaining some balance
            dataset = self.dataset_loader.get_stratified_sample(
                n_samples=size, 
                maintain_ratio=False,
                random_state=random_state
            )
        
        return dataset
    
    def run_performance_experiment(self, experiment_name, dataset, batch_sizes=None):
        """
        Run performance experiment with different batch sizes using real data.
        
        Args:
            experiment_name (str): Name of the experiment
            dataset (list): Real test dataset
            batch_sizes (list): Different batch sizes to test
        """
        if batch_sizes is None:
            # Resource-friendly batch sizes
            batch_sizes = [1, 2, 3, 4, 5, 6, 7] if self.resource_friendly else [1, 2, 3, 4, 5, 6, 7]
        
        # Limit batch sizes based on resource constraints
        batch_sizes = [bs for bs in batch_sizes if bs <= self.max_batch_size]
        
        print(f"🚀 Running performance experiment: {experiment_name}")
        print(f"⚙️  Resource-friendly mode: {self.resource_friendly}")
        print(f"   • Batch sizes: {batch_sizes}")
        print(f"   • Request delay: {self.request_delay}s")
        print(f"   • Batch delay: {self.batch_delay}s")
        print(f"   • Max retries: {self.max_retries}")
        
        experiment_results = {
            'experiment_name': experiment_name,
            'dataset_size': len(dataset),
            'batch_results': {},
            'started_at': datetime.now(),
            'resource_friendly': self.resource_friendly
        }
        
        for batch_size in batch_sizes:
            print(f"📊 Testing batch size: {batch_size}")
            
            batch_results = {
                'batch_size': batch_size,
                'batch_times': [],
                'successful_batches': 0,
                'failed_batches': 0,
                'total_messages': 0,
                'successful_messages': 0,
                'failed_messages': 0
            }
            
            # Process messages in batches
            batches = [dataset[i:i+batch_size] for i in range(0, len(dataset), batch_size)]
            
            # Limit number of batches for resource management
            max_batches = 5 if self.resource_friendly else 10
            test_batches = batches[:max_batches]
            
            for batch_idx, batch in enumerate(test_batches):
                batch_start_time = time.time()
                batch_success = True
                batch_successful_messages = 0
                
                for message_idx, (message, true_label) in enumerate(batch):
                    success = False
                    retry_count = 0
                    
                    while not success and retry_count < self.max_retries:
                        try:
                            # Resource-friendly delay between requests
                            if message_idx > 0 or batch_idx > 0:
                                time.sleep(self.request_delay)
                            
                            response = requests.post(
                                'http://localhost:8002/api/send-message',
                                json={
                                    'message': message,
                                    'user_id': f'exp_user_{batch_idx}_{message_idx}',
                                    'username': f'ExpUser{batch_idx}_{message_idx}',
                                    'channel_id': f'exp_channel_{experiment_name}'
                                },
                                timeout=self.timeout
                            )
                            
                            if response.status_code == 200:
                                batch_successful_messages += 1
                                success = True
                            else:
                                retry_count += 1
                                if retry_count < self.max_retries:
                                    time.sleep(self.request_delay * 2)  # Longer delay on retry
                                else:
                                    batch_success = False
                        
                        except requests.exceptions.Timeout:
                            retry_count += 1
                            if retry_count < self.max_retries:
                                print(f"⏰ Timeout in batch {batch_idx + 1}, message {message_idx + 1}, retrying...")
                                time.sleep(self.request_delay * 3)
                            else:
                                batch_success = False
                        
                        except requests.exceptions.RequestException as e:
                            retry_count += 1
                            if retry_count < self.max_retries:
                                print(f"🔌 Connection error in batch {batch_idx + 1}, retrying...")
                                time.sleep(self.request_delay * 2)
                            else:
                                batch_success = False
                                break
                
                batch_time = time.time() - batch_start_time
                batch_results['batch_times'].append(batch_time)
                batch_results['total_messages'] += len(batch)
                batch_results['successful_messages'] += batch_successful_messages
                batch_results['failed_messages'] += len(batch) - batch_successful_messages
                
                if batch_success:
                    batch_results['successful_batches'] += 1
                else:
                    batch_results['failed_batches'] += 1
                
                print(f"  Batch {batch_idx + 1} completed in {batch_time:.2f}s ({batch_successful_messages}/{len(batch)} messages successful)")
                
                # Batch delay for resource management
                if batch_idx < len(test_batches) - 1:
                    time.sleep(self.batch_delay)
            
            experiment_results['batch_results'][batch_size] = batch_results
        
        experiment_results['completed_at'] = datetime.now()
        experiment_results['duration'] = (experiment_results['completed_at'] - experiment_results['started_at']).total_seconds()
        
        self.results[experiment_name] = experiment_results
        return experiment_results
    
    def analyze_experiment_results(self, experiment_name):
        """
        Analyze experiment results and generate insights.
        
        Args:
            experiment_name (str): Name of the experiment to analyze
        """
        if experiment_name not in self.results:
            print(f"❌ No results found for experiment: {experiment_name}")
            return None
        
        results = self.results[experiment_name]
        print(f"📊 Analyzing experiment results: {experiment_name}")
        
        analysis = {
            'experiment_name': experiment_name,
            'dataset_size': results['dataset_size'],
            'total_duration': results['duration'],
            'resource_friendly': results['resource_friendly'],
            'batch_analysis': {}
        }
        
        for batch_size, batch_data in results['batch_results'].items():
            batch_times = batch_data['batch_times']
            
            batch_analysis = {
                'batch_size': batch_size,
                'avg_batch_time': np.mean(batch_times),
                'median_batch_time': np.median(batch_times),
                'std_batch_time': np.std(batch_times),
                'min_batch_time': np.min(batch_times),
                'max_batch_time': np.max(batch_times),
                'total_batches': len(batch_times),
                'successful_batches': batch_data['successful_batches'],
                'failed_batches': batch_data['failed_batches'],
                'batch_success_rate': batch_data['successful_batches'] / len(batch_times) if batch_times else 0,
                'total_messages': batch_data['total_messages'],
                'successful_messages': batch_data['successful_messages'],
                'failed_messages': batch_data['failed_messages'],
                'message_success_rate': batch_data['successful_messages'] / batch_data['total_messages'] if batch_data['total_messages'] > 0 else 0,
                'throughput': batch_data['successful_messages'] / np.sum(batch_times) if batch_times else 0  # messages per second
            }
            
            analysis['batch_analysis'][batch_size] = batch_analysis
            
            print(f"  Batch Size {batch_size}:")
            print(f"    • Avg Time: {batch_analysis['avg_batch_time']:.2f}s")
            print(f"    • Success Rate: {batch_analysis['message_success_rate']:.1%}")
            print(f"    • Throughput: {batch_analysis['throughput']:.2f} msg/s")
        
        return analysis
    
    def create_experiment_visualization(self, experiment_name, output_dir="reports"):
        """
        Create comprehensive visualization of experiment results.
        
        Args:
            experiment_name (str): Name of the experiment
            output_dir (str): Output directory for visualizations
        """
        if experiment_name not in self.results:
            print(f"❌ No results found for experiment: {experiment_name}")
            return None
        
        analysis = self.analyze_experiment_results(experiment_name)
        if not analysis:
            return None
        
        # Create figure with subplots
        fig = plt.figure(figsize=(16, 12))
        
        # Extract data for plotting
        batch_sizes = list(analysis['batch_analysis'].keys())
        avg_times = [analysis['batch_analysis'][bs]['avg_batch_time'] for bs in batch_sizes]
        success_rates = [analysis['batch_analysis'][bs]['message_success_rate'] for bs in batch_sizes]
        throughputs = [analysis['batch_analysis'][bs]['throughput'] for bs in batch_sizes]
        
        # 1. Average Batch Processing Time
        ax1 = plt.subplot(2, 3, 1)
        bars1 = ax1.bar(batch_sizes, avg_times, color='skyblue', alpha=0.7)
        ax1.set_title('Average Batch Processing Time\n(Real Dataset)')
        ax1.set_xlabel('Batch Size')
        ax1.set_ylabel('Time (seconds)')
        
        # Add value labels
        for bar, value in zip(bars1, avg_times):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{value:.2f}s', ha='center', va='bottom')
        
        # 2. Message Success Rate
        ax2 = plt.subplot(2, 3, 2)
        bars2 = ax2.bar(batch_sizes, success_rates, color='lightgreen', alpha=0.7)
        ax2.set_title('Message Success Rate\n(Real Dataset)')
        ax2.set_xlabel('Batch Size')
        ax2.set_ylabel('Success Rate')
        ax2.set_ylim(0, 1)
        
        # Add value labels
        for bar, value in zip(bars2, success_rates):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.1%}', ha='center', va='bottom')
        
        # 3. Throughput Analysis
        ax3 = plt.subplot(2, 3, 3)
        bars3 = ax3.bar(batch_sizes, throughputs, color='lightcoral', alpha=0.7)
        ax3.set_title('Processing Throughput\n(Real Dataset)')
        ax3.set_xlabel('Batch Size')
        ax3.set_ylabel('Messages/Second')
        
        # Add value labels
        for bar, value in zip(bars3, throughputs):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.2f}', ha='center', va='bottom')
        
        # 4. Batch Time Distribution
        ax4 = plt.subplot(2, 3, 4)
        all_times = []
        labels = []
        for bs in batch_sizes:
            times = self.results[experiment_name]['batch_results'][bs]['batch_times']
            all_times.extend(times)
            labels.extend([f'Batch {bs}'] * len(times))
        
        if all_times:
            df_times = pd.DataFrame({'Time': all_times, 'Batch Size': labels})
            sns.boxplot(data=df_times, x='Batch Size', y='Time', ax=ax4)
            ax4.set_title('Batch Time Distribution\n(Real Dataset)')
            ax4.set_ylabel('Time (seconds)')
        
        # 5. Resource Efficiency
        ax5 = plt.subplot(2, 3, 5)
        efficiency = [sr / at if at > 0 else 0 for sr, at in zip(success_rates, avg_times)]
        bars5 = ax5.bar(batch_sizes, efficiency, color='gold', alpha=0.7)
        ax5.set_title('Resource Efficiency\n(Success Rate / Time)')
        ax5.set_xlabel('Batch Size')
        ax5.set_ylabel('Efficiency Score')
        
        # Add value labels
        for bar, value in zip(bars5, efficiency):
            ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                    f'{value:.3f}', ha='center', va='bottom')
        
        # 6. Experiment Summary
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')
        
        # Calculate overall statistics
        total_messages = sum(analysis['batch_analysis'][bs]['total_messages'] for bs in batch_sizes)
        total_successful = sum(analysis['batch_analysis'][bs]['successful_messages'] for bs in batch_sizes)
        overall_success_rate = total_successful / total_messages if total_messages > 0 else 0
        
        summary_text = f"""Experiment Summary:
        
Dataset: Real SetFit/toxic_conversations
Total Messages: {total_messages:,}
Successful: {total_successful:,}
Overall Success Rate: {overall_success_rate:.1%}

Resource Configuration:
Mode: {'Resource-Friendly' if analysis['resource_friendly'] else 'Standard'}
Request Delay: {self.request_delay}s
Batch Delay: {self.batch_delay}s
Max Retries: {self.max_retries}

Best Performance:
Batch Size: {batch_sizes[throughputs.index(max(throughputs))]}
Max Throughput: {max(throughputs):.2f} msg/s
Best Success Rate: {max(success_rates):.1%}

Duration: {analysis['total_duration']:.1f} seconds"""
        
        ax6.text(0.1, 0.9, summary_text, transform=ax6.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/experiment_{experiment_name}_real.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Experiment visualization saved for {experiment_name}")
        return analysis

if __name__ == "__main__":
    # Example usage with real dataset
    print("🧪 Experimental Design - Real Dataset")
    print("=" * 50)
    
    try:
        # Initialize experimental design with resource-friendly mode
        designer = ExperimentalDesign(resource_friendly=True)
        
        # Create experiment
        designer.create_experiment(
            name="Real_Dataset_Performance",
            description="Performance analysis using real SetFit/toxic_conversations data",
            parameters={
                "dataset_source": "SetFit/toxic_conversations",
                "sample_size": 30,  # Small sample for testing
                "sampling_strategy": "balanced",
                "resource_friendly": True
            }
        )
        
        # Generate test dataset from real data
        dataset = designer.get_experimental_dataset(size=30, strategy='balanced')
        
        # Run experiment with resource-friendly batch sizes
        results = designer.run_performance_experiment("Real_Dataset_Performance", dataset, batch_sizes=[1, 2, 3, 4, 5, 6, 7])
        
        # Analyze results
        analysis = designer.analyze_experiment_results("Real_Dataset_Performance")
        
        # Create visualization
        designer.create_experiment_visualization("Real_Dataset_Performance")
        
        print("\n✅ Experimental analysis completed successfully!")
        print("📊 Check reports/ directory for visualizations")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure:")
        print("1. dissertation-experiment-data.csv exists")
        print("2. Moderation system is running on localhost:8000")
        print("3. Dataset loader is properly configured")
