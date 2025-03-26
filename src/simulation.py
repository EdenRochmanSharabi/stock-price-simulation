"""
Main simulation module for stock price modeling with regime switching,
jump diffusion, and earnings shocks.
"""
import numpy as np
import pandas as pd
from datetime import datetime
from numba import jit, prange
import time
import os

from src.data_retrieval import (
    fetch_stock_data, 
    get_market_parameters, 
    get_earnings_dates
)
from src.regime_switching import (
    RegimeSwitchingModel, 
    generate_regime_path, 
    get_regime_parameters_jit
)
from src.jump_diffusion import (
    JumpDiffusionModel, 
    generate_jump_diffusion_path,
    calibrate_jump_parameters
)
from src.earnings_shocks import (
    EarningsShockModel, 
    apply_earnings_shocks_to_path,
    estimate_earnings_shock_parameters
)
from src.utils import (
    generate_dates, 
    plot_simulated_paths, 
    plot_histogram,
    plot_regime_transitions,
    plot_jump_events,
    save_simulation_results
)

def setup_simulation(ticker, start_date=None, n_steps=252, dt=1/252,
                    use_calibration=True, regime_matrix=None, 
                    lambda_=0.1, mu_j=-0.05, sigma_j=0.1,
                    shock_mean=0.0, shock_std=0.05):
    """
    Set up simulation parameters based on historical data or user inputs.
    
    Parameters:
    -----------
    ticker : str
        Stock ticker symbol
    start_date : str or datetime, optional
        Start date for simulation (default: today)
    n_steps : int, optional
        Number of time steps (default: 252)
    dt : float, optional
        Time step size in years (default: 1/252)
    use_calibration : bool, optional
        Whether to calibrate parameters from historical data (default: True)
    regime_matrix : numpy.ndarray, optional
        2x2 transition probability matrix for regime switching model
    lambda_ : float, optional
        Jump intensity parameter (default: 0.1)
    mu_j : float, optional
        Mean jump size parameter (default: -0.05)
    sigma_j : float, optional
        Jump size volatility parameter (default: 0.1)
    shock_mean : float, optional
        Mean earnings shock parameter (default: 0.0)
    shock_std : float, optional
        Earnings shock volatility parameter (default: 0.05)
    
    Returns:
    --------
    dict
        Dictionary of simulation parameters
    """
    # Generate simulation dates
    dates = generate_dates(start_date, n_steps)
    
    # Get market parameters from historical data
    market_params = get_market_parameters(ticker)
    
    if market_params is None:
        raise ValueError(f"Failed to retrieve market parameters for {ticker}")
    
    # Extract parameters
    initial_price = market_params['initial_price']
    base_drift = market_params['drift']
    base_volatility = market_params['volatility']
    
    # Get earnings dates
    earnings_dates = market_params.get('earnings_dates', [])
    
    # Set up regime switching model
    if regime_matrix is None:
        # Default transition matrix
        regime_matrix = np.array([
            [0.90, 0.10],  # Bear: 90% stay, 10% switch to bull
            [0.05, 0.95]   # Bull: 5% switch to bear, 95% stay
        ])
    
    # Calibrate jump diffusion parameters if needed
    if use_calibration:
        # Fetch historical data
        stock_data = fetch_stock_data(ticker, period="2y")
        
        if stock_data is not None:
            # Calculate returns
            returns = stock_data['Adj Close'].pct_change().dropna().values
            
            # Calibrate jump parameters
            lambda_, mu_j, sigma_j = calibrate_jump_parameters(returns, dt)
            
            # Estimate earnings shock parameters
            shock_mean, shock_std = estimate_earnings_shock_parameters(
                stock_data, earnings_dates
            )
    
    # Compile parameters
    params = {
        'ticker': ticker,
        'initial_price': initial_price,
        'base_drift': base_drift,
        'base_volatility': base_volatility,
        'n_steps': n_steps,
        'dt': dt,
        'regime_matrix': regime_matrix,
        'lambda': lambda_,
        'mu_j': mu_j,
        'sigma_j': sigma_j,
        'shock_mean': shock_mean,
        'shock_std': shock_std,
        'earnings_dates': earnings_dates,
        'dates': dates,
        'start_date': dates[0].strftime('%Y-%m-%d'),
        'end_date': dates[-1].strftime('%Y-%m-%d')
    }
    
    return params

@jit(nopython=True)
def simulate_path_with_regimes_jumps(initial_price, n_steps, dt, 
                                    regime_path, base_drift, base_volatility,
                                    jump_indicators, jump_sizes):
    """
    Simulate a single price path with regime switching and jumps.
    
    Parameters:
    -----------
    initial_price : float
        Initial stock price
    n_steps : int
        Number of time steps
    dt : float
        Time step size in years
    regime_path : numpy.ndarray
        Array of regime indices (0 for bear, 1 for bull)
    base_drift : float
        Base drift parameter
    base_volatility : float
        Base volatility parameter
    jump_indicators : numpy.ndarray
        Boolean array indicating jump events
    jump_sizes : numpy.ndarray
        Array of jump sizes
        
    Returns:
    --------
    numpy.ndarray
        Simulated stock price path
    """
    # Initialize price path
    prices = np.zeros(n_steps)
    prices[0] = initial_price
    
    # Simulate price path
    for t in range(1, n_steps):
        # Get regime-specific parameters
        drift, vol = get_regime_parameters_jit(regime_path[t], base_drift, base_volatility)
        
        # Convert annualized parameters to time step
        drift_dt = drift * dt
        vol_dt = vol * np.sqrt(dt)
        
        # Generate random shock
        z = np.random.normal(0, 1)
        
        # Update price using GBM without jumps
        prices[t] = prices[t-1] * np.exp(drift_dt - 0.5 * vol_dt**2 + vol_dt * z)
        
        # Apply jump if it occurs
        if jump_indicators[t]:
            prices[t] *= (1 + jump_sizes[t])
    
    return prices

@jit(nopython=True, parallel=True)
def simulate_multiple_paths(n_paths, initial_price, n_steps, dt, 
                           regime_matrix, initial_regime, base_drift, base_volatility,
                           lambda_, mu_j, sigma_j):
    """
    Simulate multiple price paths with regime switching and jumps.
    
    Parameters:
    -----------
    n_paths : int
        Number of simulation paths
    initial_price : float
        Initial stock price
    n_steps : int
        Number of time steps
    dt : float
        Time step size in years
    regime_matrix : numpy.ndarray
        2x2 transition probability matrix
    initial_regime : int
        Initial regime (0 for bear, 1 for bull)
    base_drift : float
        Base drift parameter
    base_volatility : float
        Base volatility parameter
    lambda_ : float
        Jump intensity parameter
    mu_j : float
        Mean jump size parameter
    sigma_j : float
        Jump size volatility parameter
        
    Returns:
    --------
    numpy.ndarray
        Array of simulated paths with shape (n_paths, n_steps)
    """
    # Initialize array for paths
    paths = np.zeros((n_paths, n_steps))
    
    # Simulate paths in parallel
    for i in prange(n_paths):
        # Generate regime path
        regime_path = generate_regime_path(regime_matrix, initial_regime, n_steps)
        
        # Generate jump process
        jump_indicators, jump_sizes = generate_jump_diffusion_path(
            n_steps, dt, lambda_, mu_j, sigma_j
        )
        
        # Simulate path
        paths[i] = simulate_path_with_regimes_jumps(
            initial_price, n_steps, dt, regime_path, 
            base_drift, base_volatility, jump_indicators, jump_sizes
        )
    
    return paths

def apply_earnings_shocks(paths, dates, earnings_dates, shock_mean, shock_std):
    """
    Apply earnings shocks to simulated paths.
    
    Parameters:
    -----------
    paths : numpy.ndarray
        Array of simulated paths with shape (n_paths, n_steps)
    dates : array-like
        Dates corresponding to time steps
    earnings_dates : list
        List of earnings announcement dates
    shock_mean : float
        Mean earnings shock parameter
    shock_std : float
        Earnings shock volatility parameter
        
    Returns:
    --------
    numpy.ndarray
        Updated paths with earnings shocks applied
    """
    n_paths, n_steps = paths.shape
    updated_paths = paths.copy()
    
    # Apply earnings shocks to each path
    for i in range(n_paths):
        updated_paths[i], _ = apply_earnings_shocks_to_path(
            paths[i], dates, earnings_dates, shock_mean, shock_std
        )
    
    return updated_paths

def run_simulation(ticker="AAPL", n_paths=1000, n_steps=252, dt=1/252, 
                  start_date=None, use_calibration=True,
                  save_results=True, show_plots=True):
    """
    Run a full stock price simulation with regime switching, jump diffusion,
    and earnings shocks.
    
    Parameters:
    -----------
    ticker : str, optional
        Stock ticker symbol (default: "AAPL")
    n_paths : int, optional
        Number of simulation paths (default: 1000)
    n_steps : int, optional
        Number of time steps (default: 252)
    dt : float, optional
        Time step size in years (default: 1/252)
    start_date : str or datetime, optional
        Start date for simulation (default: today)
    use_calibration : bool, optional
        Whether to calibrate parameters from historical data (default: True)
    save_results : bool, optional
        Whether to save simulation results (default: True)
    show_plots : bool, optional
        Whether to show plots (default: True)
        
    Returns:
    --------
    dict
        Dictionary of simulation results
    """
    print(f"Starting simulation for {ticker}...")
    start_time = time.time()
    
    # Set up simulation parameters
    params = setup_simulation(
        ticker, start_date, n_steps, dt, use_calibration
    )
    
    # Extract parameters
    initial_price = params['initial_price']
    base_drift = params['base_drift']
    base_volatility = params['base_volatility']
    regime_matrix = params['regime_matrix']
    lambda_ = params['lambda']
    mu_j = params['mu_j']
    sigma_j = params['sigma_j']
    shock_mean = params['shock_mean']
    shock_std = params['shock_std']
    earnings_dates = params['earnings_dates']
    dates = params['dates']
    
    # Choose initial regime (randomly select based on steady state)
    p_bear = regime_matrix[1, 0] / (regime_matrix[0, 1] + regime_matrix[1, 0])
    initial_regime = np.random.choice([0, 1], p=[p_bear, 1-p_bear])
    
    print(f"Simulating {n_paths} paths with regime switching and jump diffusion...")
    
    # Run multiple simulations
    paths = simulate_multiple_paths(
        n_paths, initial_price, n_steps, dt, regime_matrix, initial_regime,
        base_drift, base_volatility, lambda_, mu_j, sigma_j
    )
    
    print("Applying earnings shocks...")
    
    # Apply earnings shocks if available
    if earnings_dates:
        paths = apply_earnings_shocks(paths, dates, earnings_dates, shock_mean, shock_std)
    
    # Calculate statistics
    final_prices = paths[:, -1]
    mean_final = np.mean(final_prices)
    median_final = np.median(final_prices)
    p5 = np.percentile(final_prices, 5)
    p95 = np.percentile(final_prices, 95)
    
    print(f"Simulation completed in {time.time() - start_time:.2f} seconds")
    print(f"Mean final price: ${mean_final:.2f}")
    print(f"Median final price: ${median_final:.2f}")
    print(f"90% confidence interval: [${p5:.2f}, ${p95:.2f}]")
    
    # Create visualizations if requested
    if show_plots:
        # Plot simulated paths
        fig = plot_simulated_paths(
            paths, dates, title=f"Simulated Stock Paths for {ticker}",
            percentiles=[5, 50, 95]
        )
        
        # Plot histogram of final prices
        fig = plot_histogram(
            final_prices, title=f"Distribution of Final Stock Prices for {ticker}"
        )
    
    # Save results if requested
    if save_results:
        results_dir = save_simulation_results(paths, dates, params, ticker)
        print(f"Results saved to {results_dir}")
    
    # Return results
    results = {
        'paths': paths,
        'dates': dates,
        'final_prices': final_prices,
        'statistics': {
            'mean': mean_final,
            'median': median_final,
            'p5': p5,
            'p95': p95
        },
        'params': params
    }
    
    return results

if __name__ == "__main__":
    # Example usage
    results = run_simulation(ticker="AAPL", n_paths=1000, show_plots=True) 