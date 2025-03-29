#!/usr/bin/env python3

"""
Plots Module
-----------
Functions for creating visualizations of simulation results.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def set_plotting_style():
    """Set consistent styling for all plots."""
    # Set seaborn style
    sns.set(style="whitegrid", palette="muted", context="talk")
    
    # Set matplotlib parameters
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['axes.titlesize'] = 18
    plt.rcParams['axes.titleweight'] = 'bold'
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12
    plt.rcParams['legend.fontsize'] = 12


def create_price_path_plot(ticker, paths, statistics, sample_size=100):
    """
    Create a plot of price paths.
    
    Args:
        ticker (str): Stock ticker symbol
        paths (numpy.ndarray): Array of price paths
        statistics (dict): Simulation statistics
        sample_size (int): Number of paths to sample for display
        
    Returns:
        matplotlib.figure.Figure: The generated figure
    """
    set_plotting_style()
    
    # Create figure
    fig, ax = plt.subplots()
    
    # Get a random sample of paths to plot
    if paths.shape[0] > sample_size:
        indices = np.random.choice(paths.shape[0], sample_size, replace=False)
        sample_paths = paths[indices]
    else:
        sample_paths = paths
    
    # Get the initial price
    initial_price = statistics['initial_price']
    
    # Plot sample paths
    for i in range(sample_paths.shape[0]):
        ax.plot(range(sample_paths.shape[1]), sample_paths[i], alpha=0.1, color='blue')
    
    # Plot mean path
    mean_path = np.mean(paths, axis=0)
    ax.plot(range(mean_path.shape[0]), mean_path, linewidth=2.5, color='red', label='Mean Price')
    
    # Plot percentiles
    percentiles = [10, 50, 90]
    colors = ['#FF8C00', '#32CD32', '#4169E1']
    
    for i, p in enumerate(percentiles):
        percentile_path = np.percentile(paths, p, axis=0)
        ax.plot(range(percentile_path.shape[0]), percentile_path, linewidth=1.5, 
                linestyle='--', color=colors[i], label=f'{p}th Percentile')
    
    # Set labels and title
    ax.set_xlabel('Days')
    ax.set_ylabel('Price ($)')
    ax.set_title(f'{ticker} - Price Path Simulation')
    
    # Add legend
    ax.legend()
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Customize y-axis
    ax.set_ylim(bottom=0, top=None)
    
    # Add text box with key statistics
    stats_text = (
        f"Initial Price: ${initial_price:.2f}\n"
        f"Expected Return: {statistics['expected_return']:.2f}%\n"
        f"Probability of Profit: {statistics['prob_profit']:.1f}%\n"
        f"VaR (95%): ${statistics['var_95']:.2f}"
    )
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    return fig


def create_distribution_plot(ticker, paths, statistics):
    """
    Create a distribution plot of final prices.
    
    Args:
        ticker (str): Stock ticker symbol
        paths (numpy.ndarray): Array of price paths
        statistics (dict): Simulation statistics
        
    Returns:
        matplotlib.figure.Figure: The generated figure
    """
    set_plotting_style()
    
    # Get final prices
    final_prices = paths[:, -1]
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Plot histogram of final prices
    sns.histplot(final_prices, kde=True, color='blue', ax=ax1)
    ax1.axvline(statistics['initial_price'], color='red', linestyle='--', 
                label=f"Initial (${statistics['initial_price']:.2f})")
    ax1.axvline(statistics['mean_final_price'], color='green', linestyle='-', 
                label=f"Mean (${statistics['mean_final_price']:.2f})")
    
    # Add percentile lines
    percentiles = ['25%', '50%', '75%']
    colors = ['purple', 'orange', 'brown']
    
    for i, p in enumerate(percentiles):
        if p in statistics['percentiles']:
            ax1.axvline(statistics['percentiles'][p], color=colors[i], 
                       linestyle=':', label=f"{p} (${statistics['percentiles'][p]:.2f})")
    
    ax1.set_xlabel('Final Price ($)')
    ax1.set_ylabel('Frequency')
    ax1.set_title(f'{ticker} - Final Price Distribution')
    ax1.legend()
    
    # Plot histogram of returns
    returns = (final_prices / statistics['initial_price'] - 1) * 100
    sns.histplot(returns, kde=True, color='green', ax=ax2)
    ax2.axvline(0, color='red', linestyle='--', label='0% Return')
    ax2.axvline(statistics['expected_return'], color='blue', linestyle='-', 
               label=f"Mean ({statistics['expected_return']:.2f}%)")
    
    ax2.set_xlabel('Return (%)')
    ax2.set_ylabel('Frequency')
    ax2.set_title(f'{ticker} - Return Distribution')
    ax2.legend()
    
    plt.tight_layout()
    return fig


def generate_plots(ticker, paths, statistics, output_dir):
    """
    Generate and save plots for simulation results.
    
    Args:
        ticker (str): Stock ticker symbol
        paths (numpy.ndarray): Array of price paths
        statistics (dict): Simulation statistics
        output_dir (str): Directory to save plots
        
    Returns:
        dict: Paths to saved plots
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Create and save price path plot
    price_fig = create_price_path_plot(ticker, paths, statistics)
    price_path = os.path.join(output_dir, f"{ticker}_paths.png")
    price_fig.savefig(price_path)
    plt.close(price_fig)
    
    # Create and save distribution plot
    dist_fig = create_distribution_plot(ticker, paths, statistics)
    dist_path = os.path.join(output_dir, f"{ticker}_distribution.png")
    dist_fig.savefig(dist_path)
    plt.close(dist_fig)
    
    print(f"Generated plots for {ticker} saved to:")
    print(f"  - Price paths: {price_path}")
    print(f"  - Distribution: {dist_path}")
    
    return {
        'paths': price_path,
        'distribution': dist_path
    } 