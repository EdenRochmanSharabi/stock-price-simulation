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


def save_simulation_data(ticker, simulation_paths, statistics, output_dir):
    """
    Save simulation data to disk.
    
    Args:
        ticker (str): Stock ticker symbol
        simulation_paths (numpy.ndarray): Simulation paths
        statistics (dict): Calculated statistics
        output_dir (str): Directory to save files
        
    Returns:
        dict: Paths to saved files
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save paths data as CSV
    paths_file = os.path.join(output_dir, f"{ticker}_paths.csv")
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
    
    print(f"Saved simulation data for {ticker} to:")
    print(f"  - Paths: {paths_file}")
    print(f"  - Statistics: {stats_file}")
    print(f"  - Sample paths: {sample_file}")
    
    return {
        'paths': paths_file,
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
    
    # Check if files exist
    if not os.path.exists(paths_file) or not os.path.exists(stats_file):
        print(f"Data files for {ticker} not found in {data_dir}")
        return None, None
    
    # Load paths data
    simulation_paths = pd.read_csv(paths_file).values
    
    # Load statistics
    with open(stats_file, 'r') as f:
        statistics = json.load(f)
    
    return simulation_paths, statistics 