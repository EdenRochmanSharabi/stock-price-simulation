#!/usr/bin/env python3

"""
Statistics and Visualization
---------------------------
Functions for calculating statistics and generating visualizations from simulation results.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json


def calculate_statistics(ticker, simulation_paths, initial_price):
    """
    Calculate comprehensive statistics from simulation results.
    
    Args:
        ticker (str): Stock ticker symbol
        simulation_paths (numpy.ndarray): Array of simulated price paths
        initial_price (float): Initial stock price
        
    Returns:
        dict: Calculated statistics
    """
    # Final prices (last column of each path)
    final_prices = simulation_paths[:, -1]
    
    # Calculate returns for each path
    returns = (final_prices / initial_price - 1) * 100
    log_returns = np.log(final_prices / initial_price) * 100
    
    # Calculate basic statistics
    mean_final_price = np.mean(final_prices)
    median_final_price = np.median(final_prices)
    std_final_price = np.std(final_prices)
    min_final_price = np.min(final_prices)
    max_final_price = np.max(final_prices)
    
    # Calculate percentiles
    percentiles = {
        "1%": float(np.percentile(final_prices, 1)),
        "5%": float(np.percentile(final_prices, 5)),
        "10%": float(np.percentile(final_prices, 10)),
        "25%": float(np.percentile(final_prices, 25)),
        "50%": float(np.percentile(final_prices, 50)),
        "75%": float(np.percentile(final_prices, 75)),
        "90%": float(np.percentile(final_prices, 90)),
        "95%": float(np.percentile(final_prices, 95)),
        "99%": float(np.percentile(final_prices, 99))
    }
    
    # Calculate potential returns
    expected_return = (mean_final_price / initial_price - 1) * 100
    median_return = (median_final_price / initial_price - 1) * 100
    
    # Calculate risk measures
    var_95 = initial_price - percentiles["5%"]  # 95% Value at Risk (absolute dollar amount)
    var_99 = initial_price - percentiles["1%"]  # 99% Value at Risk
    
    # Calculate probability of profit/loss
    prob_profit = np.mean(final_prices > initial_price) * 100
    prob_loss = np.mean(final_prices < initial_price) * 100
    
    # Calculate probability of significant moves
    prob_up_10percent = np.mean(final_prices > initial_price * 1.1) * 100
    prob_up_20percent = np.mean(final_prices > initial_price * 1.2) * 100
    prob_down_10percent = np.mean(final_prices < initial_price * 0.9) * 100
    prob_down_20percent = np.mean(final_prices < initial_price * 0.8) * 100
    
    # Advanced statistics
    try:
        from scipy import stats
        skewness = float(stats.skew(returns))
        kurtosis = float(stats.kurtosis(returns))  # Excess kurtosis
        
        # One-sample t-test (testing if returns are different from zero)
        t_stat, p_value = stats.ttest_1samp(returns, 0)
        t_stat = float(t_stat)
        p_value = float(p_value)
        
        # Normality test based on sample size
        n = len(returns)
        if n < 5000:
            # Shapiro-Wilk test for small samples
            normality_stat, normality_p = stats.shapiro(returns)
            normality_test = "Shapiro-Wilk"
        elif 5000 <= n <= 30000:
            # D'Agostino-Pearson test for medium samples
            normality_stat, normality_p = stats.normaltest(returns)
            normality_test = "D'Agostino-Pearson"
        else:
            # Anderson-Darling test for large samples
            result = stats.anderson(returns, dist='norm')
            normality_stat = result.statistic
            # Get critical values and significance levels
            critical_values = result.critical_values
            significance_levels = result.significance_level
            # Find the first significance level where we reject normality
            normality_p = 0.0
            for i, (cv, sl) in enumerate(zip(critical_values, significance_levels)):
                if normality_stat > cv:
                    normality_p = sl / 100.0  # Convert to decimal
                    break
            normality_test = "Anderson-Darling"
        
        normality_stat = float(normality_stat)
        normality_p = float(normality_p)
        
        has_scipy = True
    except ImportError:
        skewness = kurtosis = t_stat = p_value = normality_stat = normality_p = None
        has_scipy = False
    
    # Risk-adjusted return measures
    volatility = float(np.std(returns))
    
    # Sharpe ratio (assuming 0% risk-free rate for simplicity)
    sharpe_ratio = float(expected_return / volatility) if volatility > 0 else 0
    
    # Sortino ratio (using downside deviation instead of std dev)
    downside_returns = returns[returns < 0]
    downside_deviation = float(np.std(downside_returns)) if len(downside_returns) > 0 else 0.001
    sortino_ratio = float(expected_return / downside_deviation) if downside_deviation > 0 else 0
    
    # Maximum drawdown
    max_drawdown = calculate_max_drawdown(simulation_paths)
    
    # Confidence intervals for expected return (95%)
    return_std_error = volatility / np.sqrt(len(returns))
    ci_lower = float(expected_return - 1.96 * return_std_error)
    ci_upper = float(expected_return + 1.96 * return_std_error)
    
    return {
        "ticker": ticker,
        "initial_price": float(initial_price),
        "mean_final_price": float(mean_final_price),
        "median_final_price": float(median_final_price),
        "std_final_price": float(std_final_price),
        "min_final_price": float(min_final_price),
        "max_final_price": float(max_final_price),
        "percentiles": percentiles,
        "expected_return": float(expected_return),
        "median_return": float(median_return),
        "return_volatility": volatility,
        "var_95": float(var_95),
        "var_99": float(var_99),
        "prob_profit": float(prob_profit),
        "prob_loss": float(prob_loss),
        "prob_up_10percent": float(prob_up_10percent),
        "prob_up_20percent": float(prob_up_20percent),
        "prob_down_10percent": float(prob_down_10percent),
        "prob_down_20percent": float(prob_down_20percent),
        # Advanced statistics
        "skewness": skewness,
        "kurtosis": kurtosis,
        "t_stat": t_stat,
        "p_value": p_value,
        "sharpe_ratio": sharpe_ratio,
        "sortino_ratio": sortino_ratio,
        "max_drawdown": max_drawdown,
        "return_ci_lower": ci_lower,
        "return_ci_upper": ci_upper,
        "normality_stat": normality_stat,
        "normality_p": normality_p,
        "normality_test": normality_test,
        "has_scipy": has_scipy
    }


def calculate_max_drawdown(paths):
    """Calculate maximum drawdown for each path and return the average."""
    max_drawdowns = []
    
    for i in range(paths.shape[0]):
        path = paths[i, :]
        
        # Calculate the running maximum
        running_max = np.maximum.accumulate(path)
        
        # Calculate drawdown for this path
        drawdowns = (running_max - path) / running_max
        
        # Find the maximum drawdown
        max_drawdown = np.max(drawdowns)
        max_drawdowns.append(max_drawdown)
    
    # Return the average max drawdown across all paths
    return float(np.mean(max_drawdowns))


def save_simulation_data(ticker, simulation_paths, statistics, output_dir):
    """
    Save simulation data to files.
    
    Args:
        ticker (str): Stock ticker symbol
        simulation_paths (numpy.ndarray): Simulation paths data
        statistics (dict): Statistics dictionary
        output_dir (str): Base output directory
    """
    # Ensure data directory exists
    data_dir = os.path.join(output_dir, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Create DataFrame with paths
    sample_size = min(100, simulation_paths.shape[0])
    sample_paths = simulation_paths[:sample_size, :]
    
    df = pd.DataFrame(sample_paths.T)  # Transpose so each column is a path
    df.index = range(len(df))  # Use simple integer index
    df.columns = [f"Path_{i+1}" for i in range(sample_size)]
    df.index.name = "Step"
    
    # Save to CSV
    csv_file = os.path.join(data_dir, f"{ticker}_simulation_data.csv")
    df.to_csv(csv_file)
    
    # Save statistics to JSON (also in data directory)
    json_file = os.path.join(data_dir, f"{ticker}_statistics.json")
    with open(json_file, 'w') as f:
        json.dump(statistics, f, indent=2)
    
    print(f"Saved data for {ticker} to {data_dir}")


def generate_plots(ticker, simulation_paths, statistics, output_dir):
    """
    Generate and save plots from simulation results.
    
    Args:
        ticker (str): Stock ticker symbol
        simulation_paths (numpy.ndarray): Simulation paths data
        statistics (dict): Statistics dictionary
        output_dir (str): Base output directory or graphs directory
    """
    # Ensure graphs directory exists
    graphs_dir = output_dir
    if os.path.basename(output_dir) != "graphs":
        graphs_dir = os.path.join(output_dir, "graphs")
        if not os.path.exists(graphs_dir):
            os.makedirs(graphs_dir)
    
    # Set style
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # 1. Price paths plot
    plt.figure(figsize=(12, 6))
    
    # Plot a subset of paths
    for i in range(min(50, simulation_paths.shape[0])):
        plt.plot(simulation_paths[i, :], linewidth=0.8, alpha=0.3)
    
    # Calculate and plot percentiles
    percentiles = {}
    for i in range(simulation_paths.shape[1]):
        step_values = simulation_paths[:, i]
        percentiles[i] = {
            "5%": np.percentile(step_values, 5),
            "50%": np.percentile(step_values, 50),
            "95%": np.percentile(step_values, 95)
        }
    
    # Create arrays for percentile lines
    steps = list(range(simulation_paths.shape[1]))
    p05 = [percentiles[i]["5%"] for i in steps]
    p50 = [percentiles[i]["50%"] for i in steps]
    p95 = [percentiles[i]["95%"] for i in steps]
    
    # Plot percentiles
    plt.plot(p50, color='red', linewidth=2, label='Median')
    plt.plot(p05, color='blue', linewidth=2, label='5th percentile')
    plt.plot(p95, color='green', linewidth=2, label='95th percentile')
    
    # Add chart elements
    plt.title(f"{ticker} Stock Price Simulation", fontsize=16)
    plt.xlabel("Trading Days", fontsize=12)
    plt.ylabel("Price ($)", fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save plot - directly to output_dir without adding a 'graphs' subdirectory
    paths_file = os.path.join(graphs_dir, f"{ticker}_price_paths.png")
    plt.savefig(paths_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. Final price histogram
    plt.figure(figsize=(12, 6))
    
    # Get final prices
    final_prices = simulation_paths[:, -1]
    
    # Plot histogram
    sns.histplot(final_prices, kde=True, bins=50)
    
    # Add lines for key statistics
    plt.axvline(statistics["initial_price"], color='black', linestyle='--', label='Initial Price')
    plt.axvline(statistics["mean_final_price"], color='red', linestyle='-', label='Mean')
    plt.axvline(statistics["percentiles"]["5%"], color='blue', linestyle='-', label='5th Percentile')
    plt.axvline(statistics["percentiles"]["95%"], color='green', linestyle='-', label='95th Percentile')
    
    # Add chart elements
    plt.title(f"{ticker} Final Price Distribution", fontsize=16)
    plt.xlabel("Price ($)", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save histogram - directly to output_dir without adding a 'graphs' subdirectory
    hist_file = os.path.join(graphs_dir, f"{ticker}_price_histogram.png")
    plt.savefig(hist_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. Return Distribution
    plt.figure(figsize=(12, 6))
    
    # Calculate returns
    returns = (final_prices / statistics["initial_price"] - 1) * 100
    
    # Plot return histogram
    sns.histplot(returns, kde=True, bins=50, color='purple')
    
    # Add vertical lines
    plt.axvline(0, color='black', linestyle='--', label='No Change')
    plt.axvline(statistics["expected_return"], color='red', linestyle='-', label=f'Mean: {statistics["expected_return"]:.2f}%')
    
    # Add confidence interval if available
    if "return_ci_lower" in statistics and statistics["return_ci_lower"] is not None:
        plt.axvline(statistics["return_ci_lower"], color='orange', linestyle=':', label=f'95% CI: {statistics["return_ci_lower"]:.2f}%')
        plt.axvline(statistics["return_ci_upper"], color='orange', linestyle=':', label=f'{statistics["return_ci_upper"]:.2f}%')
    
    plt.title(f"{ticker} Return Distribution", fontsize=16)
    plt.xlabel("Return (%)", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save return histogram - directly to output_dir without adding a 'graphs' subdirectory
    return_hist_file = os.path.join(graphs_dir, f"{ticker}_return_histogram.png")
    plt.savefig(return_hist_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. QQ Plot (checks if returns follow normal distribution)
    try:
        from scipy import stats
        plt.figure(figsize=(10, 10))
        
        # Create QQ plot
        res = stats.probplot(returns, plot=plt)
        
        plt.title(f"{ticker} Return QQ Plot (Normal Distribution Test)", fontsize=16)
        plt.xlabel("Theoretical Quantiles", fontsize=12)
        plt.ylabel("Sample Quantiles", fontsize=12)
        
        # Add text with Shapiro-Wilk test results
        if statistics.get("normality_p") is not None:
            normality_p = statistics["normality_p"]
            is_normal = "Normal" if normality_p > 0.05 else "Not Normal"
            plt.figtext(0.15, 0.85, f"Normality Test: {statistics['normality_test']}\nNormality p-value: {normality_p:.4f}\nDistribution is {is_normal} (α=0.05)", 
                       bbox=dict(facecolor='white', alpha=0.8))
        
        plt.grid(True, alpha=0.3)
        
        # Save QQ plot - directly to output_dir without adding a 'graphs' subdirectory
        qq_file = os.path.join(graphs_dir, f"{ticker}_qq_plot.png")
        plt.savefig(qq_file, dpi=300, bbox_inches='tight')
        plt.close()
    except ImportError:
        print(f"Scipy not available, skipping QQ plot for {ticker}")
    
    # 5. Box plot of returns
    plt.figure(figsize=(8, 6))
    
    # Select a sample of paths (e.g., first 20)
    sample_size = min(30, simulation_paths.shape[0])
    sample_paths = simulation_paths[:sample_size, :]
    
    # Calculate returns for each step in each path
    step_returns = np.zeros((sample_size, simulation_paths.shape[1]-1))
    for i in range(sample_size):
        path = sample_paths[i, :]
        step_returns[i, :] = np.diff(path) / path[:-1] * 100
    
    # Create box plot
    plt.boxplot(step_returns, sym='o', whis=1.5)
    plt.axhline(0, color='black', linestyle='--', alpha=0.3)
    
    plt.title(f"{ticker} Daily Returns Distribution", fontsize=16)
    plt.xlabel("Time Step", fontsize=12)
    plt.ylabel("Daily Return (%)", fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Save box plot - directly to output_dir without adding a 'graphs' subdirectory
    box_file = os.path.join(graphs_dir, f"{ticker}_returns_boxplot.png")
    plt.savefig(box_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    # 6. Risk-Reward Scatterplot
    plt.figure(figsize=(12, 6))
    
    # Calculate returns and risk for groups of paths
    groups = min(25, simulation_paths.shape[0] // 10)  # Divide paths into groups
    paths_per_group = simulation_paths.shape[0] // groups
    
    group_returns = []
    group_risks = []
    
    for i in range(groups):
        start_idx = i * paths_per_group
        end_idx = (i + 1) * paths_per_group
        
        group_paths = simulation_paths[start_idx:end_idx, :]
        group_final_prices = group_paths[:, -1]
        group_return = (np.mean(group_final_prices) / statistics["initial_price"] - 1) * 100
        group_risk = np.std(group_final_prices) / statistics["initial_price"] * 100
        
        group_returns.append(group_return)
        group_risks.append(group_risk)
    
    # Plot the risk-reward scatter
    plt.scatter(group_risks, group_returns, alpha=0.7, s=50, c=group_returns, cmap='viridis')
    plt.colorbar(label='Expected Return (%)')
    
    plt.title(f"{ticker} Risk-Reward Analysis", fontsize=16)
    plt.xlabel("Risk (Volatility %)", fontsize=12)
    plt.ylabel("Expected Return (%)", fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Save risk-reward plot - directly to output_dir without adding a 'graphs' subdirectory
    risk_file = os.path.join(graphs_dir, f"{ticker}_risk_reward.png")
    plt.savefig(risk_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Generated plots for {ticker}") 