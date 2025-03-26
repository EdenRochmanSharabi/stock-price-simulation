"""
Utility functions for stock price simulation.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os

def generate_dates(start_date=None, n_steps=252, freq='B'):
    """
    Generate a sequence of business dates.
    
    Parameters:
    -----------
    start_date : str or datetime, optional
        Start date (default: today)
    n_steps : int, optional
        Number of dates to generate (default: 252)
    freq : str, optional
        Frequency of dates (default: 'B' for business days)
        
    Returns:
    --------
    pd.DatetimeIndex
        Sequence of dates
    """
    if start_date is None:
        start_date = datetime.now().strftime('%Y-%m-%d')
        
    return pd.date_range(start=start_date, periods=n_steps, freq=freq)

def calculate_returns(prices):
    """
    Calculate returns from price series.
    
    Parameters:
    -----------
    prices : numpy.ndarray or pandas.Series
        Price series
        
    Returns:
    --------
    numpy.ndarray or pandas.Series
        Return series
    """
    if isinstance(prices, pd.Series):
        return prices.pct_change().dropna()
    else:
        returns = np.diff(prices) / prices[:-1]
        return returns

def plot_simulated_paths(paths, dates=None, title="Simulated Stock Paths", 
                         ylabel="Stock Price", figsize=(12, 6), max_paths=10,
                         percentiles=None, save_path=None):
    """
    Plot simulated stock price paths.
    
    Parameters:
    -----------
    paths : numpy.ndarray
        Array of simulated paths with shape (n_paths, n_steps)
    dates : array-like, optional
        Dates for x-axis
    title : str, optional
        Plot title (default: "Simulated Stock Paths")
    ylabel : str, optional
        Y-axis label (default: "Stock Price")
    figsize : tuple, optional
        Figure size (default: (12, 6))
    max_paths : int, optional
        Maximum number of individual paths to plot (default: 10)
    percentiles : list, optional
        Percentiles to plot (default: None)
    save_path : str, optional
        Path to save the figure (default: None)
        
    Returns:
    --------
    matplotlib.figure.Figure
        Plot figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    n_paths, n_steps = paths.shape
    
    # Create date index if not provided
    if dates is None:
        dates = np.arange(n_steps)
    
    # Plot a subset of individual paths
    plot_paths = min(n_paths, max_paths)
    for i in range(plot_paths):
        ax.plot(dates, paths[i], alpha=0.5, linewidth=1)
    
    # Plot percentiles if requested
    if percentiles is not None:
        for p in percentiles:
            percentile_values = np.percentile(paths, p, axis=0)
            ax.plot(dates, percentile_values, 'k--', linewidth=2, 
                    label=f"{p}th percentile")
    
    # Plot mean path
    mean_path = np.mean(paths, axis=0)
    ax.plot(dates, mean_path, 'r-', linewidth=2, label="Mean")
    
    # Format dates if DatetimeIndex
    if isinstance(dates, pd.DatetimeIndex):
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
    
    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    ax.grid(True)
    
    plt.tight_layout()
    
    # Save figure if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

def plot_histogram(final_prices, bins=50, title="Distribution of Final Stock Prices", 
                  xlabel="Stock Price", figsize=(10, 6), save_path=None):
    """
    Plot a histogram of final stock prices.
    
    Parameters:
    -----------
    final_prices : numpy.ndarray
        Array of final stock prices
    bins : int, optional
        Number of bins (default: 50)
    title : str, optional
        Plot title (default: "Distribution of Final Stock Prices")
    xlabel : str, optional
        X-axis label (default: "Stock Price")
    figsize : tuple, optional
        Figure size (default: (10, 6))
    save_path : str, optional
        Path to save the figure (default: None)
        
    Returns:
    --------
    matplotlib.figure.Figure
        Plot figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.hist(final_prices, bins=bins, alpha=0.7, color='blue', edgecolor='black')
    
    # Add vertical lines for mean and percentiles
    mean_price = np.mean(final_prices)
    median_price = np.median(final_prices)
    p5 = np.percentile(final_prices, 5)
    p95 = np.percentile(final_prices, 95)
    
    ax.axvline(mean_price, color='r', linestyle='--', linewidth=2, label=f"Mean: {mean_price:.2f}")
    ax.axvline(median_price, color='g', linestyle='--', linewidth=2, label=f"Median: {median_price:.2f}")
    ax.axvline(p5, color='k', linestyle=':', linewidth=2, label=f"5th percentile: {p5:.2f}")
    ax.axvline(p95, color='k', linestyle=':', linewidth=2, label=f"95th percentile: {p95:.2f}")
    
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Frequency")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

def plot_regime_transitions(regime_path, dates=None, title="Market Regime Transitions", 
                           figsize=(12, 4), save_path=None):
    """
    Plot regime transitions.
    
    Parameters:
    -----------
    regime_path : numpy.ndarray
        Array of regime indices (0 for bear, 1 for bull)
    dates : array-like, optional
        Dates for x-axis
    title : str, optional
        Plot title (default: "Market Regime Transitions")
    figsize : tuple, optional
        Figure size (default: (12, 4))
    save_path : str, optional
        Path to save the figure (default: None)
        
    Returns:
    --------
    matplotlib.figure.Figure
        Plot figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create date index if not provided
    if dates is None:
        dates = np.arange(len(regime_path))
    
    # Plot regime as a step function (0 for bear, 1 for bull)
    ax.step(dates, regime_path, where='post', color='blue', linewidth=2)
    
    # Add horizontal lines for regimes
    ax.axhline(y=0, color='r', linestyle='--', alpha=0.5, label="Bear Market")
    ax.axhline(y=1, color='g', linestyle='--', alpha=0.5, label="Bull Market")
    
    # Format dates if DatetimeIndex
    if isinstance(dates, pd.DatetimeIndex):
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
    
    ax.set_xlabel("Date")
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Bear", "Bull"])
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

def plot_jump_events(stock_prices, jump_indicators, jump_sizes, dates=None,
                    title="Stock Price with Jump Events", figsize=(12, 6), save_path=None):
    """
    Plot stock price path with jump events.
    
    Parameters:
    -----------
    stock_prices : numpy.ndarray
        Array of stock prices
    jump_indicators : numpy.ndarray
        Boolean array indicating jump events
    jump_sizes : numpy.ndarray
        Array of jump sizes
    dates : array-like, optional
        Dates for x-axis
    title : str, optional
        Plot title (default: "Stock Price with Jump Events")
    figsize : tuple, optional
        Figure size (default: (12, 6))
    save_path : str, optional
        Path to save the figure (default: None)
        
    Returns:
    --------
    matplotlib.figure.Figure
        Plot figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create date index if not provided
    if dates is None:
        dates = np.arange(len(stock_prices))
    
    # Plot stock price path
    ax.plot(dates, stock_prices, 'b-', linewidth=2, label="Stock Price")
    
    # Highlight jump events
    jump_indices = np.where(jump_indicators)[0]
    jump_dates = [dates[i] for i in jump_indices]
    jump_prices = stock_prices[jump_indices]
    
    # Calculate marker colors based on jump size
    colors = ['g' if jump_sizes[i] > 0 else 'r' for i in jump_indices]
    
    # Plot jump events
    ax.scatter(jump_dates, jump_prices, c=colors, s=100, alpha=0.7,
              marker='o', edgecolors='k', zorder=5)
    
    # Format dates if DatetimeIndex
    if isinstance(dates, pd.DatetimeIndex):
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
    
    ax.set_xlabel("Date")
    ax.set_ylabel("Stock Price")
    ax.set_title(title)
    
    # Add colored markers to legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='b', lw=2, label='Stock Price'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='g', markersize=10,
               markeredgecolor='k', label='Positive Jump'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='r', markersize=10,
               markeredgecolor='k', label='Negative Jump')
    ]
    ax.legend(handles=legend_elements)
    
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save figure if path provided
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig

def save_simulation_results(paths, dates, params, ticker, results_dir='../results'):
    """
    Save simulation results to files.
    
    Parameters:
    -----------
    paths : numpy.ndarray
        Array of simulated paths
    dates : array-like
        Dates for simulations
    params : dict
        Simulation parameters
    ticker : str
        Stock ticker
    results_dir : str, optional
        Directory to save results (default: '../results')
        
    Returns:
    --------
    str
        Path to saved results directory
    """
    # Create results directory if it doesn't exist
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # Create a subdirectory for this simulation
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    sim_dir = os.path.join(results_dir, f"{ticker}_{timestamp}")
    os.makedirs(sim_dir)
    
    # Save paths as numpy array
    np.save(os.path.join(sim_dir, 'simulated_paths.npy'), paths)
    
    # Save dates as numpy array
    if isinstance(dates, pd.DatetimeIndex):
        dates_array = dates.to_numpy()
    else:
        dates_array = np.array(dates)
    np.save(os.path.join(sim_dir, 'dates.npy'), dates_array)
    
    # Save parameters as text file
    with open(os.path.join(sim_dir, 'parameters.txt'), 'w') as f:
        f.write("Simulation Parameters:\n")
        f.write("=====================\n\n")
        
        for key, value in params.items():
            f.write(f"{key}: {value}\n")
    
    # Create visualizations
    
    # Plot simulated paths
    fig = plot_simulated_paths(
        paths, dates, title=f"Simulated Stock Paths for {ticker}",
        percentiles=[5, 50, 95],
        save_path=os.path.join(sim_dir, 'simulated_paths.png')
    )
    plt.close(fig)
    
    # Plot histogram of final prices
    final_prices = paths[:, -1]
    fig = plot_histogram(
        final_prices, title=f"Distribution of Final Stock Prices for {ticker}",
        save_path=os.path.join(sim_dir, 'final_price_distribution.png')
    )
    plt.close(fig)
    
    return sim_dir 