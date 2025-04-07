#!/usr/bin/env python3

"""
Statistics Module
---------------
Statistical analysis functions for simulation results.
"""

import numpy as np
from typing import Dict, Union, Optional


def calculate_max_drawdown(paths: np.ndarray) -> float:
    """
    Calculate the average of maximum drawdowns across paths.
    
    Args:
        paths (numpy.ndarray): Simulation paths array
        
    Returns:
        float: Average of maximum drawdowns across paths
    """
    if not isinstance(paths, np.ndarray) or paths.size == 0:
        return 0.0
        
    paths = paths.astype(np.float64)  # Ensure float type
    max_drawdowns = []
    
    for i in range(paths.shape[0]):
        path = paths[i, :]
        
        # Skip paths with non-positive or non-finite values
        if np.any(~np.isfinite(path)) or np.any(path <= 0):
            max_drawdowns.append(1.0)  # Maximum possible drawdown
            continue
            
        # Calculate running maximum
        running_max = np.maximum.accumulate(path)
        
        # Calculate drawdowns where running_max > 0
        valid_indices = running_max > 0
        if not np.any(valid_indices):
            max_drawdowns.append(1.0)
            continue
            
        drawdowns = np.zeros_like(path, dtype=np.float64)
        drawdowns[valid_indices] = (running_max[valid_indices] - path[valid_indices]) / running_max[valid_indices]
        
        max_drawdown = np.nanmax(drawdowns)
        if np.isfinite(max_drawdown):
            max_drawdowns.append(float(max_drawdown))
        else:
            max_drawdowns.append(1.0)
    
    if not max_drawdowns:
        return 0.0
        
    return float(np.mean(max_drawdowns))  # Return average of maximum drawdowns


def calculate_max_drawdown_across_paths(paths: np.ndarray) -> float:
    """
    Calculate the maximum drawdown across all paths.
    
    Args:
        paths (numpy.ndarray): Simulation paths array
        
    Returns:
        float: Maximum drawdown across all paths
    """
    if not isinstance(paths, np.ndarray) or paths.size == 0:
        return 0.0
        
    paths = paths.astype(np.float64)  # Ensure float type
    max_drawdowns = []
    
    for i in range(paths.shape[0]):
        path = paths[i, :]
        print(f"Path {i+1}: {path}")  # Debug: Print each path
        
        # Skip paths with non-positive or non-finite values
        if np.any(~np.isfinite(path)) or np.any(path <= 0):
            print(f"Path {i+1}: Invalid values, setting max drawdown to 1.0")  # Debug
            max_drawdowns.append(1.0)  # Maximum possible drawdown
            continue
            
        # Calculate running maximum
        running_max = np.maximum.accumulate(path)
        print(f"Path {i+1}: Running max: {running_max}")  # Debug
        
        # Calculate drawdowns where running_max > 0
        valid_indices = running_max > 0
        if not np.any(valid_indices):
            print(f"Path {i+1}: No valid indices, setting max drawdown to 1.0")  # Debug
            max_drawdowns.append(1.0)
            continue
            
        drawdowns = np.zeros_like(path, dtype=np.float64)
        drawdowns[valid_indices] = (running_max[valid_indices] - path[valid_indices]) / running_max[valid_indices]
        print(f"Path {i+1}: Drawdowns: {drawdowns}")  # Debug
        
        max_drawdown = np.nanmax(drawdowns)
        if np.isfinite(max_drawdown):
            print(f"Path {i+1}: Max drawdown: {max_drawdown}")  # Debug
            max_drawdowns.append(float(max_drawdown))
        else:
            print(f"Path {i+1}: Non-finite max drawdown, setting to 1.0")  # Debug
            max_drawdowns.append(1.0)
    
    if not max_drawdowns:
        return 0.0
        
    result = float(np.max(max_drawdowns))
    print(f"Final max drawdown across all paths: {result}")  # Debug
    return result


def calculate_statistics(ticker: str, simulation_paths: np.ndarray, initial_price: float) -> Dict[str, Union[float, Dict[str, float], Optional[float]]]:
    """
    Calculate comprehensive statistics from simulation results.
    
    Args:
        ticker (str): Stock ticker symbol
        simulation_paths (numpy.ndarray): Array of simulated price paths
        initial_price (float): Initial stock price
        
    Returns:
        dict: Calculated statistics
    """
    # Handle edge cases
    if not isinstance(simulation_paths, np.ndarray) or simulation_paths.size == 0:
        raise ValueError("Empty or invalid simulation paths")
    if initial_price <= 0:
        raise ValueError("Initial price must be positive")
    
    # Ensure float type for calculations
    simulation_paths = simulation_paths.astype(np.float64)
    
    # Final prices (last column of each path)
    final_prices = simulation_paths[:, -1].copy()
    
    # Replace infinite or negative values with NaN
    final_prices[~np.isfinite(final_prices)] = np.nan
    final_prices[final_prices <= 0] = np.nan
    
    # Calculate returns for each path
    valid_prices = final_prices[np.isfinite(final_prices)]
    if len(valid_prices) == 0:
        raise ValueError("No valid prices in simulation paths")
    
    returns = np.zeros_like(final_prices)
    valid_mask = np.isfinite(final_prices)
    returns[valid_mask] = (final_prices[valid_mask] / initial_price - 1) * 100
    
    # Calculate log returns safely
    log_returns = np.zeros_like(final_prices)
    log_returns[valid_mask] = np.log(final_prices[valid_mask] / initial_price) * 100
    
    # Calculate basic statistics
    mean_final_price = float(np.nanmean(final_prices))
    median_final_price = float(np.nanmedian(final_prices))
    std_final_price = float(np.nanstd(final_prices))
    min_final_price = float(np.nanmin(final_prices))
    max_final_price = float(np.nanmax(final_prices))
    
    # Calculate percentiles safely
    percentiles = {
        "1%": float(np.nanpercentile(final_prices, 1)),
        "5%": float(np.nanpercentile(final_prices, 5)),
        "10%": float(np.nanpercentile(final_prices, 10)),
        "25%": float(np.nanpercentile(final_prices, 25)),
        "50%": float(np.nanpercentile(final_prices, 50)),
        "75%": float(np.nanpercentile(final_prices, 75)),
        "90%": float(np.nanpercentile(final_prices, 90)),
        "95%": float(np.nanpercentile(final_prices, 95)),
        "99%": float(np.nanpercentile(final_prices, 99))
    }
    
    # Calculate potential returns
    expected_return = float((mean_final_price / initial_price - 1) * 100)
    median_return = float((median_final_price / initial_price - 1) * 100)
    
    # Calculate risk measures
    var_95 = float(initial_price - percentiles["5%"])  # 95% Value at Risk
    var_99 = float(initial_price - percentiles["1%"])  # 99% Value at Risk
    
    # Calculate probability of profit/loss
    total_valid = np.sum(valid_mask)
    if total_valid > 0:
        # Calculate probabilities based on final prices compared to initial price
        final_prices_valid = final_prices[valid_mask]
        
        # Calculate probabilities - treat unchanged as loss
        prob_profit = float(np.sum(final_prices_valid > initial_price) / total_valid * 100)
        prob_loss = float(np.sum(final_prices_valid <= initial_price) / total_valid * 100)
        prob_unchanged = 0.0  # We don't distinguish unchanged paths
        
        # No need to normalize since prob_profit + prob_loss = 100% by definition
    else:
        prob_profit = prob_loss = prob_unchanged = 0.0
    
    # Calculate probability of significant moves
    prob_up_10percent = float(np.sum((final_prices > initial_price * 1.1) & valid_mask) / total_valid * 100) if total_valid > 0 else 0.0
    prob_up_20percent = float(np.sum((final_prices > initial_price * 1.2) & valid_mask) / total_valid * 100) if total_valid > 0 else 0.0
    prob_down_10percent = float(np.sum((final_prices < initial_price * 0.9) & valid_mask) / total_valid * 100) if total_valid > 0 else 0.0
    prob_down_20percent = float(np.sum((final_prices < initial_price * 0.8) & valid_mask) / total_valid * 100) if total_valid > 0 else 0.0
    
    # Calculate max drawdown using the new function
    max_drawdown = calculate_max_drawdown_across_paths(simulation_paths)
    
    # Advanced statistics
    try:
        from scipy import stats
        valid_returns = returns[valid_mask]
        if len(valid_returns) > 1:
            skewness = float(stats.skew(valid_returns))
            kurtosis = float(stats.kurtosis(valid_returns))  # Excess kurtosis
            
            # One-sample t-test (testing if returns are different from zero)
            t_stat, p_value = stats.ttest_1samp(valid_returns, 0)
            t_stat = float(t_stat)
            p_value = float(p_value)
            
            # Normality test based on sample size
            n = len(valid_returns)
            if n < 5000:
                # Shapiro-Wilk test for small samples
                normality_stat, normality_p = stats.shapiro(valid_returns)
                normality_test = "Shapiro-Wilk"
            elif 5000 <= n <= 30000:
                # D'Agostino-Pearson test for medium samples
                normality_stat, normality_p = stats.normaltest(valid_returns)
                normality_test = "D'Agostino-Pearson"
            else:
                # Anderson-Darling test for large samples
                result = stats.anderson(valid_returns, dist='norm')
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
        else:
            skewness = kurtosis = t_stat = p_value = normality_stat = normality_p = None
            normality_test = None
        
        has_scipy = True
    except ImportError:
        skewness = kurtosis = t_stat = p_value = normality_stat = normality_p = None
        normality_test = None
        has_scipy = False
    
    # Risk-adjusted return measures
    volatility = float(np.nanstd(returns))
    
    # Sharpe ratio (assuming 0% risk-free rate for simplicity)
    sharpe_ratio = float(expected_return / volatility) if volatility > 0 else 0.0
    
    # Sortino ratio (using downside deviation instead of std dev)
    downside_returns = returns[returns < 0]
    downside_deviation = float(np.nanstd(downside_returns)) if len(downside_returns) > 0 else 0.001
    sortino_ratio = float(expected_return / downside_deviation) if downside_deviation > 0 else 0.0
    
    # Confidence intervals for expected return (95%)
    valid_count = np.sum(valid_mask)
    if valid_count > 1:
        return_std_error = volatility / np.sqrt(valid_count)
        ci_lower = float(expected_return - 1.96 * return_std_error)
        ci_upper = float(expected_return + 1.96 * return_std_error)
    else:
        ci_lower = ci_upper = expected_return
    
    return {
        "ticker": ticker,
        "initial_price": float(initial_price),
        "mean_final_price": mean_final_price,
        "median_final_price": median_final_price,
        "std_final_price": std_final_price,
        "min_final_price": min_final_price,
        "max_final_price": max_final_price,
        "percentiles": percentiles,
        "expected_return": expected_return,
        "median_return": median_return,
        "return_volatility": volatility,
        "var_95": var_95,
        "var_99": var_99,
        "prob_profit": prob_profit,
        "prob_loss": prob_loss,
        "prob_unchanged": prob_unchanged,
        "prob_up_10percent": prob_up_10percent,
        "prob_up_20percent": prob_up_20percent,
        "prob_down_10percent": prob_down_10percent,
        "prob_down_20percent": prob_down_20percent,
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
        "has_scipy": has_scipy,
        "valid_paths_percentage": float(valid_count / len(final_prices) * 100)
    } 