#!/usr/bin/env python3

"""
Data Storage Module
-----------------
Functions for saving and loading simulation data.
"""

import os
import json
import numpy as np
import pandas as pd


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types."""
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def save_simulation_data(ticker, simulation_paths, statistics, output_dir, save_full_paths=True):
    """
    Save simulation data to disk.
    
    Args:
        ticker (str): Stock ticker symbol
        simulation_paths (numpy.ndarray): Simulation paths
        statistics (dict): Calculated statistics
        output_dir (str): Directory to save files
        save_full_paths (bool): Whether to save the full paths matrix (can be large)
        
    Returns:
        dict: Paths to saved files
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save paths data as CSV only if save_full_paths is True
    paths_file = os.path.join(output_dir, f"{ticker}_paths.csv")
    if save_full_paths:
        pd.DataFrame(simulation_paths).to_csv(paths_file, index=False)
    
    # Save statistics as JSON
    stats_file = os.path.join(output_dir, f"{ticker}_stats.json")
    with open(stats_file, 'w') as f:
        json.dump(statistics, f, cls=NumpyEncoder, indent=2)
    
    # Save a sample of paths for quicker loading
    sample_paths = simulation_paths[np.random.choice(simulation_paths.shape[0], 
                                                   min(100, simulation_paths.shape[0]), 
                                                   replace=False)]
    sample_file = os.path.join(output_dir, f"{ticker}_sample_paths.csv")
    pd.DataFrame(sample_paths).to_csv(sample_file, index=False)
    
    if save_full_paths:
        print(f"Saved simulation data for {ticker} to:")
        print(f"  - Paths: {paths_file}")
        print(f"  - Statistics: {stats_file}")
        print(f"  - Sample paths: {sample_file}")
    else:
        print(f"Saved simulation data for {ticker} (without full paths) to:")
        print(f"  - Statistics: {stats_file}")
        print(f"  - Sample paths: {sample_file}")
    
    return {
        'paths': paths_file if save_full_paths else None,
        'stats': stats_file,
        'sample': sample_file
    }


def load_simulation_data(ticker, data_dir):
    """
    Load saved simulation data.
    
    Args:
        ticker (str): Stock ticker symbol
        data_dir (str): Directory containing saved data
        
    Returns:
        tuple: (simulation_paths, statistics)
    """
    # Construct file paths
    paths_file = os.path.join(data_dir, f"{ticker}_paths.csv")
    stats_file = os.path.join(data_dir, f"{ticker}_stats.json")
    sample_file = os.path.join(data_dir, f"{ticker}_sample_paths.csv")
    
    # Check if files exist
    if not os.path.exists(stats_file):
        print(f"Data files for {ticker} not found in {data_dir}")
        return None, None
    
    # Load paths data if available, otherwise use sample
    if os.path.exists(paths_file):
        simulation_paths = pd.read_csv(paths_file).values
    elif os.path.exists(sample_file):
        simulation_paths = pd.read_csv(sample_file).values
        print(f"Warning: Using sample paths for {ticker}, full paths not available.")
    else:
        print(f"No path data available for {ticker}")
        simulation_paths = None
    
    # Load statistics
    with open(stats_file, 'r') as f:
        statistics = json.load(f)
    
    return simulation_paths, statistics


def cleanup_raw_data(ticker=None, data_dir=None):
    """
    Delete raw path data files to save disk space after analysis is complete.
    
    Args:
        ticker (str, optional): Specific ticker to clean up. If None, clean all tickers.
        data_dir (str): Directory containing saved data
        
    Returns:
        int: Number of files deleted
    """
    if data_dir is None or not os.path.exists(data_dir):
        print("Data directory not found")
        return 0
    
    deleted_count = 0
    
    if ticker:
        # Delete specific ticker's paths file
        paths_file = os.path.join(data_dir, f"{ticker}_paths.csv")
        if os.path.exists(paths_file):
            os.remove(paths_file)
            deleted_count += 1
            print(f"Deleted raw data file: {paths_file}")
    else:
        # Delete all paths files in the directory
        for filename in os.listdir(data_dir):
            if filename.endswith("_paths.csv") and not filename.endswith("_sample_paths.csv"):
                file_path = os.path.join(data_dir, filename)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
    
    print(f"Cleanup complete. Deleted {deleted_count} raw data files.")
    return deleted_count 