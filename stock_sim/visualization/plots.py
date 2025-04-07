#!/usr/bin/env python3

"""
Plots Module
-----------
Functions for creating visualizations of simulation results.
"""

# Set non-interactive backend before importing matplotlib
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for thread safety

import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
import yfinance as yf
from datetime import datetime


def set_plotting_style():
    """Set consistent styling for all plots."""
    # Use seaborn-whitegrid style from the old version
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Set matplotlib parameters
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 10


def create_price_path_plot(ticker, paths, statistics, sample_size=50):
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
        ax.plot(range(sample_paths.shape[1]), sample_paths[i], alpha=0.3, linewidth=0.8)
    
    # Calculate percentiles for each time step
    steps = list(range(paths.shape[1]))
    p05 = [np.percentile(paths[:, i], 5) for i in steps]
    p50 = [np.percentile(paths[:, i], 50) for i in steps]
    p95 = [np.percentile(paths[:, i], 95) for i in steps]
    
    # Plot percentiles using the original color scheme
    ax.plot(steps, p50, color='red', linewidth=2, label='Median')
    ax.plot(steps, p05, color='blue', linewidth=2, label='5th percentile')
    ax.plot(steps, p95, color='green', linewidth=2, label='95th percentile')
    
    # Set labels and title
    ax.set_xlabel('Trading Days', fontsize=12)
    ax.set_ylabel('Price ($)', fontsize=12)
    ax.set_title(f'{ticker} Stock Price Simulation', fontsize=16)
    
    # Add legend
    ax.legend()
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
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
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
    # Plot histogram of final prices
    sns.histplot(final_prices, kde=True, ax=ax1)
    ax1.axvline(statistics['initial_price'], color='black', linestyle='--', 
                label=f"Initial Price")
    ax1.axvline(statistics['mean_final_price'], color='red', linestyle='-', 
                label=f"Mean")
    
    # Add percentile lines with original colors
    ax1.axvline(statistics['percentiles']["5%"], color='blue', linestyle='-', 
              label=f"5th Percentile")
    ax1.axvline(statistics['percentiles']["95%"], color='green', linestyle='-', 
              label=f"95th Percentile")
    
    ax1.set_xlabel('Price ($)', fontsize=12)
    ax1.set_ylabel('Frequency', fontsize=12)
    ax1.set_title(f'{ticker} Final Price Distribution', fontsize=16)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot histogram of returns
    returns = (final_prices / statistics['initial_price'] - 1) * 100
    sns.histplot(returns, kde=True, color='purple', ax=ax2)
    ax2.axvline(0, color='black', linestyle='--', label='No Change')
    ax2.axvline(statistics['expected_return'], color='red', linestyle='-', 
               label=f"Mean: {statistics['expected_return']:.2f}%")
    
    ax2.set_xlabel('Return (%)', fontsize=12)
    ax2.set_ylabel('Frequency', fontsize=12)
    ax2.set_title(f'{ticker} Return Distribution', fontsize=16)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def create_return_histogram_plot(ticker, paths, statistics):
    """
    Create a detailed return histogram with normal distribution overlay.
    
    Args:
        ticker (str): Stock ticker symbol
        paths (numpy.ndarray): Array of price paths
        statistics (dict): Simulation statistics
        
    Returns:
        matplotlib.figure.Figure: The generated figure
    """
    set_plotting_style()
    
    # Get final prices and calculate returns
    final_prices = paths[:, -1]
    returns = (final_prices / statistics['initial_price'] - 1) * 100
    
    # Create figure
    fig, ax = plt.subplots()
    
    # Plot histogram with KDE
    sns.histplot(returns, kde=True, color='purple', ax=ax)
    
    # Add vertical lines for important values
    ax.axvline(0, color='black', linestyle='--', label='No Change')
    ax.axvline(statistics['expected_return'], color='red', linestyle='-', 
              label=f'Mean: {statistics["expected_return"]:.2f}%')
    
    # Add confidence interval if available
    if "return_ci_lower" in statistics and statistics["return_ci_lower"] is not None:
        ax.axvline(statistics["return_ci_lower"], color='orange', linestyle=':', 
                  label=f'95% CI: {statistics["return_ci_lower"]:.2f}%')
        ax.axvline(statistics["return_ci_upper"], color='orange', linestyle=':', 
                  label=f'{statistics["return_ci_upper"]:.2f}%')
    
    # Set labels and title
    ax.set_xlabel('Return (%)', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title(f'{ticker} Return Distribution', fontsize=16)
    
    # Add legend
    ax.legend()
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def create_qq_plot(ticker, paths, statistics):
    """
    Create a Q-Q plot to check normality of returns.
    
    Args:
        ticker (str): Stock ticker symbol
        paths (numpy.ndarray): Array of price paths
        statistics (dict): Simulation statistics
        
    Returns:
        matplotlib.figure.Figure: The generated figure
    """
    set_plotting_style()
    
    # Get final prices and calculate returns
    final_prices = paths[:, -1]
    returns = (final_prices / statistics['initial_price'] - 1) * 100
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Create Q-Q plot
    res = stats.probplot(returns, plot=ax)
    
    # Set labels and title
    ax.set_xlabel('Theoretical Quantiles', fontsize=12)
    ax.set_ylabel('Sample Quantiles', fontsize=12)
    ax.set_title(f'{ticker} Return QQ Plot (Normal Distribution Test)', fontsize=16)
    
    # Add text with Shapiro-Wilk test results if available
    if statistics.get("normality_p") is not None:
        normality_p = statistics["normality_p"]
        is_normal = "Normal" if normality_p > 0.05 else "Not Normal"
        ax.text(0.15, 0.85, f"Normality Test: {statistics.get('normality_test', 'Shapiro-Wilk')}\nNormality p-value: {normality_p:.4f}\nDistribution is {is_normal} (α=0.05)", 
               bbox=dict(facecolor='white', alpha=0.8), transform=ax.transAxes)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def create_returns_boxplot(ticker, paths, statistics):
    """
    Create a boxplot of returns across time steps.
    
    Args:
        ticker (str): Stock ticker symbol
        paths (numpy.ndarray): Array of price paths
        statistics (dict): Simulation statistics
        
    Returns:
        matplotlib.figure.Figure: The generated figure
    """
    set_plotting_style()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Select a sample of paths
    sample_size = min(30, paths.shape[0])
    sample_paths = paths[:sample_size, :]
    
    # Calculate returns for each step in each path
    step_returns = np.zeros((sample_size, paths.shape[1]-1))
    for i in range(sample_size):
        path = sample_paths[i, :]
        step_returns[i, :] = np.diff(path) / path[:-1] * 100
    
    # Create box plot with original styling
    ax.boxplot(step_returns, sym='o', whis=1.5)
    ax.axhline(0, color='black', linestyle='--', alpha=0.3)
    
    # Set labels and title
    ax.set_xlabel('Time Step', fontsize=12)
    ax.set_ylabel('Daily Return (%)', fontsize=12)
    ax.set_title(f'{ticker} Daily Returns Distribution', fontsize=16)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def create_risk_reward_plot(ticker, paths, statistics):
    """
    Create a risk-reward analysis plot.
    
    Args:
        ticker (str): Stock ticker symbol
        paths (numpy.ndarray): Array of price paths
        statistics (dict): Simulation statistics
        
    Returns:
        matplotlib.figure.Figure: The generated figure
    """
    set_plotting_style()
    
    # Create figure
    fig, ax = plt.subplots()
    
    # Calculate returns and risk for groups of paths following the old approach
    groups = min(25, paths.shape[0] // 10)  # Divide paths into groups
    paths_per_group = paths.shape[0] // groups
    
    group_returns = []
    group_risks = []
    
    for i in range(groups):
        start_idx = i * paths_per_group
        end_idx = (i + 1) * paths_per_group
        
        group_paths = paths[start_idx:end_idx, :]
        group_final_prices = group_paths[:, -1]
        group_return = (np.mean(group_final_prices) / statistics["initial_price"] - 1) * 100
        group_risk = np.std(group_final_prices) / statistics["initial_price"] * 100
        
        group_returns.append(group_return)
        group_risks.append(group_risk)
    
    # Plot the risk-reward scatter with viridis colormap like the original
    scatter = ax.scatter(group_risks, group_returns, alpha=0.7, s=50, c=group_returns, cmap='viridis')
    plt.colorbar(scatter, label='Expected Return (%)')
    
    # Set labels and title
    ax.set_xlabel('Risk (Volatility %)', fontsize=12)
    ax.set_ylabel('Expected Return (%)', fontsize=12)
    ax.set_title(f'{ticker} Risk-Reward Analysis', fontsize=16)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def create_yearly_returns_plot(ticker):
    """
    Create a visualization of daily returns by year, similar to the S&P 500 visualization shown.
    
    Args:
        ticker (str): Stock ticker symbol
        
    Returns:
        matplotlib.figure.Figure: The generated figure
    """
    set_plotting_style()
    
    # Define color palette for years
    year_colors = {
        2020: '#e83e8c',  # Pink
        2021: '#75c175',  # Green
        2022: '#4e73df',  # Blue
        2023: '#343a40',  # Dark gray
        2024: '#20c997',  # Teal
        2025: '#e83e8c',  # Pink (reusing for 2025)
    }
    
    # Get current year
    current_year = datetime.now().year
    
    # Download 5 years of historical data
    data = yf.download(ticker, period="5y", progress=False)
    
    # Calculate daily returns
    data['DailyReturn'] = data['Close'].pct_change() * 100
    
    # Add year column
    data['Year'] = data.index.year
    
    # Create figure
    plt.figure(figsize=(14, 10))
    
    # Filter data to include only the last 5 years + current year
    years = sorted(list(set(data['Year'])))[-6:]
    
    # Calculate the vertical positions for each year (from bottom to top)
    year_positions = {year: i for i, year in enumerate(years)}
    
    # Plot returns for each year
    for year in years:
        year_data = data[data['Year'] == year]
        
        # Skip years with insufficient data
        if len(year_data) < 5:
            continue
            
        # Get color for this year
        color = year_colors.get(year, '#777777')  # Default gray if year not in palette
        
        # Plot the points
        plt.scatter(
            year_data['DailyReturn'],  # x-values (returns)
            [year_positions[year]] * len(year_data),  # y-values (fixed for each year)
            color=color,
            alpha=0.7,
            s=50,  # Size of dots
            label=str(year)
        )
    
    # Customize y-axis to show year labels
    plt.yticks(list(year_positions.values()), list(year_positions.keys()))
    
    # Add grid lines for returns
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Set limits and labels
    plt.xlim(-12, 8)
    plt.xlabel('Daily Returns (%)', fontsize=14)
    plt.title(f'{ticker} Daily Returns by Year', fontsize=18, fontweight='bold')
    
    # Add a vertical line at 0%
    plt.axvline(0, color='black', linestyle='-', alpha=0.3)
    
    plt.tight_layout()
    return plt.gcf()


def generate_plots(ticker, paths, statistics, output_dir):
    """
    Generate and save all plots for simulation results.
    
    Args:
        ticker (str): Stock ticker symbol
        paths (numpy.ndarray): Array of price paths
        statistics (dict): Simulation statistics
        output_dir (str): Directory to save plots
        
    Returns:
        dict: Dictionary of plot file paths
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create and save price paths plot
    price_path_fig = create_price_path_plot(ticker, paths, statistics)
    price_path_file = os.path.join(output_dir, f"{ticker}_price_paths.png")
    price_path_fig.savefig(price_path_file, dpi=100)
    plt.close(price_path_fig)
    
    # Create and save distribution plot
    distribution_fig = create_distribution_plot(ticker, paths, statistics)
    distribution_file = os.path.join(output_dir, f"{ticker}_price_histogram.png")
    distribution_fig.savefig(distribution_file, dpi=100)
    plt.close(distribution_fig)
    
    # Create and save return histogram plot
    return_hist_fig = create_return_histogram_plot(ticker, paths, statistics)
    return_hist_file = os.path.join(output_dir, f"{ticker}_return_histogram.png")
    return_hist_fig.savefig(return_hist_file, dpi=100)
    plt.close(return_hist_fig)
    
    # Create and save QQ plot
    qq_fig = create_qq_plot(ticker, paths, statistics)
    qq_file = os.path.join(output_dir, f"{ticker}_qq_plot.png")
    qq_fig.savefig(qq_file, dpi=100)
    plt.close(qq_fig)
    
    # Create and save returns boxplot
    boxplot_fig = create_returns_boxplot(ticker, paths, statistics)
    boxplot_file = os.path.join(output_dir, f"{ticker}_returns_boxplot.png")
    boxplot_fig.savefig(boxplot_file, dpi=100)
    plt.close(boxplot_fig)
    
    # Create and save risk-reward plot
    risk_reward_fig = create_risk_reward_plot(ticker, paths, statistics)
    risk_reward_file = os.path.join(output_dir, f"{ticker}_risk_reward.png")
    risk_reward_fig.savefig(risk_reward_file, dpi=100)
    plt.close(risk_reward_fig)
    
    # Create and save yearly returns plot
    yearly_returns_fig = create_yearly_returns_plot(ticker)
    yearly_returns_file = os.path.join(output_dir, f"{ticker}_yearly_returns.png")
    yearly_returns_fig.savefig(yearly_returns_file, dpi=100)
    plt.close(yearly_returns_fig)
    
    # Return dictionary of plot paths
    return {
        'paths': price_path_file,
        'distribution': distribution_file,
        'return_histogram': return_hist_file,
        'qq_plot': qq_file,
        'returns_boxplot': boxplot_file,
        'risk_reward': risk_reward_file,
        'yearly_returns': yearly_returns_file
    } 