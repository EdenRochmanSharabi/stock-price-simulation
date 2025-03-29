#!/usr/bin/env python3

"""
Simulation Engine
---------------
Main functionality for running stock price simulations.
"""

import os
import json
from tqdm import tqdm
from .base import StockModel
from .models import GBMModel, JumpDiffusionModel, HybridModel
from .analytics import calculate_statistics, save_simulation_data, generate_plots


def create_directory(directory):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")


def run_simulation(ticker, model_type='gbm', paths=1000, steps=21, dt=1/252, output_dir="output",
                  reports_dir=None, graphs_dir=None, calibrate=True, lookback_period="2y", mu=None, sigma=None,
                  jump_intensity=10, jump_mean=-0.01, jump_sigma=0.02, vol_clustering=0.85):
    """
    Run a stock price simulation using specified model and parameters.
    
    Args:
        ticker (str): Stock ticker symbol
        model_type (str): Type of model to use ('gbm', 'jump', or 'combined')
        paths (int): Number of simulation paths
        steps (int): Number of time steps
        dt (float): Time step size in years
        output_dir (str): Directory for output
        reports_dir (str, optional): Directory for HTML reports
        graphs_dir (str, optional): Directory for saved graphs
        calibrate (bool): Whether to calibrate model from historical data
        lookback_period (str): Period for historical data lookup
        mu (float, optional): Drift parameter (annualized)
        sigma (float, optional): Volatility parameter (annualized)
        jump_intensity (float): Jump intensity lambda (jumps per year)
        jump_mean (float): Jump size mean
        jump_sigma (float): Jump size standard deviation
        vol_clustering (float): Volatility regime clustering parameter
        
    Returns:
        dict: Simulation results and statistics
    """
    try:
        # Create output directories - simplified to just data folder
        create_directory(os.path.join(output_dir, "data"))
        
        # Set default reports_dir and graphs_dir if not provided
        if reports_dir is None:
            reports_dir = os.path.join(output_dir, "reports")
        if graphs_dir is None:
            graphs_dir = os.path.join(output_dir, "graphs")
            
        # Create reports and graphs directories
        create_directory(reports_dir)
        create_directory(graphs_dir)
        
        # Select the appropriate model with all parameters
        if model_type == 'gbm':
            model = GBMModel(ticker, lookback_period=lookback_period, 
                          calibrate=calibrate, mu=mu, sigma=sigma)
        elif model_type == 'jump':
            model = JumpDiffusionModel(ticker, lookback_period=lookback_period, 
                                    calibrate=calibrate, mu=mu, sigma=sigma,
                                    jump_intensity=jump_intensity, 
                                    jump_mean=jump_mean, 
                                    jump_sigma=jump_sigma)
        elif model_type == 'combined':
            # Initialize the hybrid model with all parameters
            model = HybridModel(ticker, lookback_period=lookback_period, calibrate=calibrate,
                              mu=mu, sigma=sigma, vol_clustering=vol_clustering,
                              jump_intensity=jump_intensity, jump_mean=jump_mean, 
                              jump_sigma=jump_sigma)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        # Get the initial price
        initial_price = model.initial_price
        if initial_price is None or initial_price <= 0:
            raise ValueError(f"Invalid initial price for {ticker}: {initial_price}")
        
        # Run simulation with specified dt
        print(f"Running {model_type.upper()} simulation for {ticker} with {paths} paths and {steps} steps...")
        paths_matrix = model.simulate(paths=paths, steps=steps, dt=dt)
        
        if paths_matrix is None or len(paths_matrix) == 0:
            raise ValueError(f"Simulation failed to generate paths for {ticker}")
        
        # Calculate statistics
        statistics = calculate_statistics(ticker, paths_matrix, initial_price)
        if statistics is None:
            raise ValueError(f"Failed to calculate statistics for {ticker}")
        
        # Save results - Make sure we're passing the right paths
        save_simulation_data(ticker, paths_matrix, statistics, output_dir)
        
        # Generate plots directly in the graphs directory (no ticker subdirectory)
        # This avoids the double ticker issue (EXPE/EXPE)
        generate_plots(ticker, paths_matrix, statistics, graphs_dir)
        
        result = {
            'ticker': ticker,
            'model_type': model_type,
            'paths_matrix': paths_matrix,
            'statistics': statistics,
            'initial_price': initial_price,
            'model_params': {
                'mu': float(model.mu),
                'sigma': float(model.sigma),
                'jump_intensity': float(getattr(model, 'jump_intensity', jump_intensity)),
                'jump_mean': float(getattr(model, 'jump_mean', jump_mean)),
                'jump_sigma': float(getattr(model, 'jump_sigma', jump_sigma)),
                'vol_clustering': float(getattr(model, 'vol_clustering', vol_clustering))
            }
        }
        
        # Generate individual report
        try:
            from stock_simulation_engine.reporting import generate_stock_report
            
            # Add model parameters to statistics
            report_stats = statistics.copy()
            report_stats.update({
                'model_type': model_type,
                'num_paths': paths,
                'num_steps': steps,
                'dt': float(dt),
                'initial_price': float(initial_price),
                **result['model_params']
            })
            
            # Convert percentiles to strings to avoid type issues
            if 'percentiles' in report_stats:
                for key in report_stats['percentiles']:
                    report_stats['percentiles'][key] = float(report_stats['percentiles'][key])
            
            print("Report stats prepared with all required fields")
                                
            report_path = generate_stock_report(ticker, report_stats, reports_dir)
            print(f"Generated report for {ticker}: {report_path}")
        except Exception as e:
            import traceback
            print(f"Warning: Could not generate report for {ticker}: {e}")
            traceback.print_exc()
        
        return result
    
    except Exception as e:
        import traceback
        print(f"Error running simulation for {ticker}: {str(e)}")
        traceback.print_exc()
        return None 