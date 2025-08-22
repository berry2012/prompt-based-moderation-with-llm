#!/usr/bin/env python3
"""
Dataset Loader for Dissertation Experiments
==========================================

This module provides utilities to load and process the SetFit/toxic_conversations dataset
for use in moderation system evaluation and experiments.

Author: Academic Research
Date: 2025
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Optional
import os
from pathlib import Path

class DissertationDatasetLoader:
    """
    Loads and processes the dissertation experiment dataset from CSV.
    
    The dataset is expected to have columns:
    - text: The message text
    - true_label: Binary label (0=non-toxic, 1=toxic)
    """
    
    def __init__(self, csv_path: str = "dissertation-experiment-data.csv"):
        """
        Initialize the dataset loader.
        
        Args:
            csv_path (str): Path to the CSV file containing the dataset
        """
        self.csv_path = csv_path
        self.data = None
        self.loaded = False
        
    def load_dataset(self) -> pd.DataFrame:
        """
        Load the dataset from CSV file.
        
        Returns:
            pd.DataFrame: Loaded dataset
            
        Raises:
            FileNotFoundError: If the CSV file doesn't exist
            ValueError: If the CSV file doesn't have required columns
        """
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"Dataset file not found: {self.csv_path}")
        
        try:
            self.data = pd.read_csv(self.csv_path)
            print(f"📊 Loaded dataset: {len(self.data)} samples from {self.csv_path}")
            
            # Validate required columns
            required_columns = ['text', 'true_label']
            missing_columns = [col for col in required_columns if col not in self.data.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Convert labels to standard format
            self.data['label_text'] = self.data['true_label'].apply(
                lambda x: 'Toxic' if x == 1 else 'Non-Toxic'
            )
            
            # Basic statistics
            toxic_count = (self.data['true_label'] == 1).sum()
            non_toxic_count = (self.data['true_label'] == 0).sum()
            
            print(f"📈 Dataset composition:")
            print(f"   • Toxic messages: {toxic_count} ({toxic_count/len(self.data):.1%})")
            print(f"   • Non-toxic messages: {non_toxic_count} ({non_toxic_count/len(self.data):.1%})")
            
            self.loaded = True
            return self.data
            
        except Exception as e:
            raise ValueError(f"Error loading dataset: {e}")
    
    def get_balanced_sample(self, n_samples: int = 100, random_state: int = 42) -> List[Tuple[str, str]]:
        """
        Get a balanced sample from the dataset.
        
        Args:
            n_samples (int): Total number of samples to return
            random_state (int): Random seed for reproducibility
            
        Returns:
            List[Tuple[str, str]]: List of (message, label) tuples
        """
        if not self.loaded:
            self.load_dataset()
        
        np.random.seed(random_state)
        
        # Get equal numbers of toxic and non-toxic samples
        samples_per_class = n_samples // 2
        
        toxic_data = self.data[self.data['true_label'] == 1]
        non_toxic_data = self.data[self.data['true_label'] == 0]
        
        # Sample from each class
        toxic_sample = toxic_data.sample(
            n=min(samples_per_class, len(toxic_data)), 
            random_state=random_state
        )
        non_toxic_sample = non_toxic_data.sample(
            n=min(samples_per_class, len(non_toxic_data)), 
            random_state=random_state
        )
        
        # Combine and shuffle
        combined = pd.concat([toxic_sample, non_toxic_sample])
        combined = combined.sample(frac=1, random_state=random_state).reset_index(drop=True)
        
        # Convert to list of tuples
        result = [(row['text'], row['label_text']) for _, row in combined.iterrows()]
        
        print(f"📋 Created balanced sample: {len(result)} messages")
        print(f"   • Toxic: {len(toxic_sample)}")
        print(f"   • Non-toxic: {len(non_toxic_sample)}")
        
        return result
    
    def get_stratified_sample(self, n_samples: int = 200, maintain_ratio: bool = True, random_state: int = 42) -> List[Tuple[str, str]]:
        """
        Get a stratified sample maintaining the original class distribution.
        
        Args:
            n_samples (int): Total number of samples to return
            maintain_ratio (bool): Whether to maintain original class ratio
            random_state (int): Random seed for reproducibility
            
        Returns:
            List[Tuple[str, str]]: List of (message, label) tuples
        """
        if not self.loaded:
            self.load_dataset()
        
        np.random.seed(random_state)
        
        if maintain_ratio:
            # Maintain original ratio
            toxic_ratio = (self.data['true_label'] == 1).mean()
            toxic_samples = int(n_samples * toxic_ratio)
            non_toxic_samples = n_samples - toxic_samples
        else:
            # Equal samples from each class
            toxic_samples = n_samples // 2
            non_toxic_samples = n_samples // 2
        
        toxic_data = self.data[self.data['true_label'] == 1]
        non_toxic_data = self.data[self.data['true_label'] == 0]
        
        # Sample from each class
        toxic_sample = toxic_data.sample(
            n=min(toxic_samples, len(toxic_data)), 
            random_state=random_state
        )
        non_toxic_sample = non_toxic_data.sample(
            n=min(non_toxic_samples, len(non_toxic_data)), 
            random_state=random_state
        )
        
        # Combine and shuffle
        combined = pd.concat([toxic_sample, non_toxic_sample])
        combined = combined.sample(frac=1, random_state=random_state).reset_index(drop=True)
        
        # Convert to list of tuples
        result = [(row['text'], row['label_text']) for _, row in combined.iterrows()]
        
        print(f"📋 Created stratified sample: {len(result)} messages")
        print(f"   • Toxic: {len(toxic_sample)} ({len(toxic_sample)/len(result):.1%})")
        print(f"   • Non-toxic: {len(non_toxic_sample)} ({len(non_toxic_sample)/len(result):.1%})")
        
        return result
    
    def get_full_dataset(self) -> List[Tuple[str, str]]:
        """
        Get the full dataset as a list of tuples.
        
        Returns:
            List[Tuple[str, str]]: List of (message, label) tuples
        """
        if not self.loaded:
            self.load_dataset()
        
        result = [(row['text'], row['label_text']) for _, row in self.data.iterrows()]
        
        print(f"📋 Full dataset: {len(result)} messages")
        return result
    
    def get_dataset_statistics(self) -> Dict:
        """
        Get comprehensive statistics about the dataset.
        
        Returns:
            Dict: Dataset statistics
        """
        if not self.loaded:
            self.load_dataset()
        
        toxic_count = (self.data['true_label'] == 1).sum()
        non_toxic_count = (self.data['true_label'] == 0).sum()
        
        # Text length statistics
        text_lengths = self.data['text'].str.len()
        
        stats = {
            'total_samples': len(self.data),
            'toxic_samples': int(toxic_count),
            'non_toxic_samples': int(non_toxic_count),
            'toxic_ratio': float(toxic_count / len(self.data)),
            'non_toxic_ratio': float(non_toxic_count / len(self.data)),
            'text_length_stats': {
                'mean': float(text_lengths.mean()),
                'median': float(text_lengths.median()),
                'min': int(text_lengths.min()),
                'max': int(text_lengths.max()),
                'std': float(text_lengths.std())
            }
        }
        
        return stats
    
    def create_test_train_split(self, test_size: float = 0.2, random_state: int = 42) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
        """
        Create train/test split maintaining class balance.
        
        Args:
            test_size (float): Proportion of data to use for testing
            random_state (int): Random seed for reproducibility
            
        Returns:
            Tuple[List, List]: (train_data, test_data) as lists of (message, label) tuples
        """
        if not self.loaded:
            self.load_dataset()
        
        np.random.seed(random_state)
        
        # Split each class separately to maintain balance
        toxic_data = self.data[self.data['true_label'] == 1]
        non_toxic_data = self.data[self.data['true_label'] == 0]
        
        # Calculate split sizes
        toxic_test_size = int(len(toxic_data) * test_size)
        non_toxic_test_size = int(len(non_toxic_data) * test_size)
        
        # Random splits
        toxic_shuffled = toxic_data.sample(frac=1, random_state=random_state)
        non_toxic_shuffled = non_toxic_data.sample(frac=1, random_state=random_state)
        
        # Create splits
        toxic_test = toxic_shuffled[:toxic_test_size]
        toxic_train = toxic_shuffled[toxic_test_size:]
        
        non_toxic_test = non_toxic_shuffled[:non_toxic_test_size]
        non_toxic_train = non_toxic_shuffled[non_toxic_test_size:]
        
        # Combine and shuffle
        train_data = pd.concat([toxic_train, non_toxic_train]).sample(frac=1, random_state=random_state)
        test_data = pd.concat([toxic_test, non_toxic_test]).sample(frac=1, random_state=random_state)
        
        # Convert to tuples
        train_tuples = [(row['text'], row['label_text']) for _, row in train_data.iterrows()]
        test_tuples = [(row['text'], row['label_text']) for _, row in test_data.iterrows()]
        
        print(f"📊 Dataset split created:")
        print(f"   • Training: {len(train_tuples)} samples")
        print(f"   • Testing: {len(test_tuples)} samples")
        
        return train_tuples, test_tuples

# Convenience function for quick access
def load_dissertation_dataset(csv_path: str = "dissertation-experiment-data.csv") -> DissertationDatasetLoader:
    """
    Quick function to load the dissertation dataset.
    
    Args:
        csv_path (str): Path to the CSV file
        
    Returns:
        DissertationDatasetLoader: Loaded dataset loader
    """
    loader = DissertationDatasetLoader(csv_path)
    loader.load_dataset()
    return loader

if __name__ == "__main__":
    # Example usage
    print("🔬 Dissertation Dataset Loader - Example Usage")
    print("=" * 50)
    
    try:
        # Load dataset
        loader = load_dissertation_dataset()
        
        # Get statistics
        stats = loader.get_dataset_statistics()
        print(f"\n📊 Dataset Statistics:")
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for subkey, subvalue in value.items():
                    print(f"     {subkey}: {subvalue}")
            else:
                print(f"   {key}: {value}")
        
        # Get balanced sample
        sample = loader.get_balanced_sample(n_samples=20)
        print(f"\n📋 Sample messages:")
        for i, (text, label) in enumerate(sample[:3]):
            print(f"   {i+1}. [{label}] {text[:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure dissertation-experiment-data.csv exists in the current directory")
