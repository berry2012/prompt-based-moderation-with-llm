#!/usr/bin/env python3
"""
Preprocess the experiment-data.csv file for analysis.
This script cleans and formats the data for use in the moderation system evaluation.
"""

import os
import pandas as pd
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("preprocess.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def preprocess_data(data_path='experiment-data.csv', output_dir='data'):
    """
    Preprocess the experiment data CSV file.
    
    Args:
        data_path: Path to the experiment data CSV file
        output_dir: Directory to save processed data
    
    Returns:
        DataFrame containing the processed data
    """
    logger.info(f"Preprocessing file: {data_path}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Read the CSV file
        df = pd.read_csv(data_path)
        
        # Check if required columns exist
        if 'text' not in df.columns or 'true_label' not in df.columns:
            logger.error(f"Required columns 'text' and 'true_label' not found in {data_path}")
            raise ValueError(f"Required columns not found in {data_path}")
        
        # Clean the text data
        df['text'] = df['text'].apply(lambda x: x.strip() if isinstance(x, str) else x)
        
        # Remove any rows with missing values
        df = df.dropna(subset=['text', 'true_label'])
        
        # Ensure true_label is numeric
        df['true_label'] = pd.to_numeric(df['true_label'], errors='coerce')
        df = df.dropna(subset=['true_label'])
        df['true_label'] = df['true_label'].astype(int)
        
        logger.info(f"Processed {len(df)} samples")
        logger.info(f"Label distribution: {df['true_label'].value_counts().to_dict()}")
        
        # Save as CSV
        df.to_csv(f"{output_dir}/processed_dataset.csv", index=False)
        
        # Create JSON format for testing
        test_messages = []
        for idx, row in df.iterrows():
            test_messages.append({
                "message": row['text'],
                "user_id": f"test_user_{idx}",
                "username": f"TestUser{idx}",
                "channel_id": "evaluation",
                "ground_truth": "toxic" if row['true_label'] == 1 else "non_toxic"
            })
        
        # Save as JSON
        with open(f"{output_dir}/test_messages.json", 'w') as f:
            json.dump(test_messages, f, indent=2)
        
        logger.info(f"Saved processed data to {output_dir}/processed_dataset.csv and {output_dir}/test_messages.json")
        
        return df
        
    except Exception as e:
        logger.error(f"Error preprocessing data: {e}")
        raise

def analyze_dataset(df):
    """
    Analyze the dataset and print statistics.
    
    Args:
        df: DataFrame containing the dataset
    """
    logger.info("Analyzing dataset")
    
    # Basic statistics
    total_samples = len(df)
    toxic_samples = df['true_label'].sum()
    non_toxic_samples = total_samples - toxic_samples
    
    # Text length statistics
    df['text_length'] = df['text'].apply(len)
    avg_length = df['text_length'].mean()
    median_length = df['text_length'].median()
    min_length = df['text_length'].min()
    max_length = df['text_length'].max()
    
    # Print statistics
    stats = {
        "total_samples": total_samples,
        "toxic_samples": int(toxic_samples),
        "non_toxic_samples": int(non_toxic_samples),
        "toxic_percentage": float(toxic_samples / total_samples * 100),
        "avg_length": float(avg_length),
        "median_length": float(median_length),
        "min_length": int(min_length),
        "max_length": int(max_length)
    }
    
    # Save statistics
    with open("data/dataset_stats.json", 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Dataset statistics: {stats}")
    
    # Print summary
    print("\n=== Dataset Statistics ===")
    print(f"Total samples: {total_samples}")
    print(f"Toxic samples: {int(toxic_samples)} ({toxic_samples / total_samples * 100:.1f}%)")
    print(f"Non-toxic samples: {int(non_toxic_samples)} ({non_toxic_samples / total_samples * 100:.1f}%)")
    print(f"Average text length: {avg_length:.1f} characters")
    print(f"Median text length: {median_length:.1f} characters")
    print(f"Min text length: {min_length} characters")
    print(f"Max text length: {max_length} characters")
    
    return stats

if __name__ == "__main__":
    # Preprocess data
    df = preprocess_data()
    
    # Analyze dataset
    analyze_dataset(df)
    
    print("\nPreprocessing complete! Data saved to 'data' directory.")
