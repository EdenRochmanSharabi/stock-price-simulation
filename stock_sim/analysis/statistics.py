#!/usr/bin/env python3

"""
Statistics Module
---------------
Statistical analysis functions for simulation results.
"""

import numpy as np


def calculate_max_drawdown(paths):
    """
    Calculate maximum drawdown for each path and return the average.
    
    Args:
        paths (numpy.ndarray): Simulation paths array
        
    Returns:
        float: Average maximum drawdown across all paths
    """
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
        normality_test = None
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