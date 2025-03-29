#!/usr/bin/env python3

"""
Simulation Engine
----------------
Core simulation engine for running stock price simulations.
"""

import os
import json
from datetime import datetime
from .models import ModelFactory


class SimulationEngine:
    """
    Engine for running stock price simulations.
    
    This class encapsulates the process of creating and running 
    simulations with different models and parameters.
    """
    
    def __init__(self, output_base_dir="output"):
        """
        Initialize the simulation engine.
        
        Args:
            output_base_dir (str): Base directory for all simulation outputs
        """
        self._output_base_dir = output_base_dir
        self._create_output_structure()
        self._stop_requested = {}  # Track stop requests by simulation ID
        
    def _create_output_structure(self):
        """Create the output directory structure."""
        # Create main output directories
        self._reports_dir = os.path.join(self._output_base_dir, "reports")
        self._graphs_dir = os.path.join(self._output_base_dir, "graphs")
        self._data_dir = os.path.join(self._output_base_dir, "data")
        
        # Ensure directories exist
        for directory in [self._output_base_dir, self._reports_dir, self._graphs_dir, self._data_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Created directory: {directory}")
    
    def run_simulation(self, ticker, model_type='gbm', paths=1000, steps=21, dt=1/252,
                     calibrate=True, lookback_period="2y", simulation_id=None, **kwargs):
        """
        Run a stock price simulation using specified model and parameters.
        
        Args:
            ticker (str): Stock ticker symbol
            model_type (str): Type of model to use ('gbm', 'jump', or 'hybrid')
            paths (int): Number of simulation paths
            steps (int): Number of time steps
            dt (float): Time step size in years
            calibrate (bool): Whether to calibrate model from historical data
            lookback_period (str): Period for historical data lookup
            simulation_id (any): Optional ID for tracking simulation status
            **kwargs: Additional model-specific parameters
            
        Returns:
            dict: Simulation results and statistics
            
        Raises:
            Exception: If any step of the simulation process fails
        """
        try:
            # Reset stop flag if a simulation ID is provided
            if simulation_id is not None:
                self._stop_requested[simulation_id] = False
            
            # Create the model using the factory
            model = ModelFactory.create_model(
                model_type, ticker, 
                lookback_period=lookback_period,
                calibrate=calibrate,
                **kwargs
            )
            
            # Get the initial price
            initial_price = model.initial_price
            if initial_price is None or initial_price <= 0:
                raise ValueError(f"Invalid initial price for {ticker}: {initial_price}")
            
            # Run simulation
            print(f"Running {model_type.upper()} simulation for {ticker} with {paths} paths and {steps} steps...")
            paths_matrix = model.simulate(paths=paths, steps=steps, dt=dt)
            
            # Check if stop was requested
            if simulation_id is not None and self._stop_requested.get(simulation_id, False):
                print(f"Simulation {simulation_id} for {ticker} was stopped by user")
                raise InterruptedError(f"Simulation for {ticker} was stopped by user")
            
            if paths_matrix is None or len(paths_matrix) == 0:
                raise ValueError(f"Simulation failed to generate paths for {ticker}")
            
            # Calculate statistics
            from .analysis import calculate_statistics
            statistics = calculate_statistics(ticker, paths_matrix, initial_price)
            
            # Check if stop was requested
            if simulation_id is not None and self._stop_requested.get(simulation_id, False):
                print(f"Simulation {simulation_id} for {ticker} was stopped by user")
                raise InterruptedError(f"Simulation for {ticker} was stopped by user")
            
            if statistics is None:
                raise ValueError(f"Failed to calculate statistics for {ticker}")
            
            # Save simulation data
            from .analysis import save_simulation_data
            data_path = save_simulation_data(ticker, paths_matrix, statistics, self._data_dir)
            
            # Check if stop was requested
            if simulation_id is not None and self._stop_requested.get(simulation_id, False):
                print(f"Simulation {simulation_id} for {ticker} was stopped by user")
                raise InterruptedError(f"Simulation for {ticker} was stopped by user")
            
            # Generate plots
            from .visualization import generate_plots
            plot_paths = generate_plots(ticker, paths_matrix, statistics, self._graphs_dir)
            
            # Create result dictionary
            result = {
                'ticker': ticker,
                'model_type': model_type,
                'paths_matrix': paths_matrix,
                'statistics': statistics,
                'initial_price': initial_price,
                'model_params': self._get_model_params(model, model_type),
                'data_path': data_path,
                'plot_paths': plot_paths
            }
            
            # Check if stop was requested
            if simulation_id is not None and self._stop_requested.get(simulation_id, False):
                print(f"Simulation {simulation_id} for {ticker} was stopped by user")
                raise InterruptedError(f"Simulation for {ticker} was stopped by user")
            
            # Generate report if available
            report_path = self._generate_report(ticker, result)
            if report_path:
                result['report_path'] = report_path
            
            # Clean up stop tracking if simulation completed successfully
            if simulation_id is not None and simulation_id in self._stop_requested:
                del self._stop_requested[simulation_id]
            
            return result
            
        except InterruptedError:
            # Re-raise interruption errors
            raise
        except Exception as e:
            import traceback
            print(f"Error running simulation for {ticker}: {str(e)}")
            traceback.print_exc()
            raise
    
    def request_stop(self, simulation_id):
        """
        Request to stop a running simulation.
        
        Args:
            simulation_id: ID of the simulation to stop
            
        Returns:
            bool: Whether the stop request was registered
        """
        if simulation_id is None:
            return False
        
        self._stop_requested[simulation_id] = True
        print(f"Stop requested for simulation {simulation_id}")
        return True
    
    def is_stop_requested(self, simulation_id):
        """Check if stop has been requested for a simulation."""
        if simulation_id is None:
            return False
        return self._stop_requested.get(simulation_id, False)
    
    def _get_model_params(self, model, model_type):
        """Extract model parameters for result dictionary."""
        params = {
            'mu': float(model.mu),
            'sigma': float(model.sigma)
        }
        
        # Add specific parameters based on model type
        if model_type in ['jump', 'hybrid', 'combined']:
            # For jump diffusion models, add jump parameters
            jump_model = model if model_type == 'jump' else model.jump_model
            params.update({
                'jump_intensity': float(jump_model.jump_intensity),
                'jump_mean': float(jump_model.jump_mean),
                'jump_sigma': float(jump_model.jump_sigma)
            })
            
        if model_type in ['hybrid', 'combined']:
            # For hybrid models, add volatility clustering parameter
            params['vol_clustering'] = float(model.vol_clustering)
            
        return params
    
    def _generate_report(self, ticker, result):
        """Generate HTML report for the simulation results."""
        try:
            # Import the reporting module
            from .analysis import generate_stock_report
            
            # Add simulation parameters to statistics for the report
            report_stats = result['statistics'].copy()
            report_stats.update({
                'model_type': result['model_type'],
                'num_paths': len(result['paths_matrix']),
                'num_steps': result['paths_matrix'].shape[1] - 1,
                'dt': 1/252,  # Default value, modify if needed
                'initial_price': float(result['initial_price']),
                **result['model_params']
            })
            
            # Convert percentiles to strings to avoid type issues
            if 'percentiles' in report_stats:
                for key in report_stats['percentiles']:
                    report_stats['percentiles'][key] = float(report_stats['percentiles'][key])
            
            # Generate the report
            report_path = generate_stock_report(ticker, report_stats, self._reports_dir)
            print(f"Generated report for {ticker}: {report_path}")
            return report_path
            
        except Exception as e:
            import traceback
            print(f"Warning: Could not generate report for {ticker}: {e}")
            traceback.print_exc()
            return None
    
    def batch_simulate(self, tickers, model_type='gbm', paths=1000, steps=21, simulation_id=None, **kwargs):
        """
        Run simulations for multiple tickers in batch.
        
        Args:
            tickers (list): List of ticker symbols
            model_type (str): Type of model to use
            paths (int): Number of simulation paths
            steps (int): Number of time steps
            simulation_id (any): Optional ID for tracking simulation status
            **kwargs: Additional simulation parameters
            
        Returns:
            dict: Results for each ticker
        """
        results = {}
        
        # Reset stop flag if a simulation ID is provided
        if simulation_id is not None:
            self._stop_requested[simulation_id] = False
        
        for ticker in tickers:
            # Check if stop was requested
            if simulation_id is not None and self._stop_requested.get(simulation_id, False):
                print(f"Batch simulation {simulation_id} was stopped by user")
                break
                
            try:
                print(f"\nStarting simulation for {ticker}...")
                
                # Use the same simulation ID for stopping individual ticker simulations
                result = self.run_simulation(
                    ticker, model_type=model_type, 
                    paths=paths, steps=steps,
                    simulation_id=simulation_id,
                    **kwargs
                )
                results[ticker] = result
                print(f"Completed {ticker} simulation")
            except InterruptedError:
                # Stop was requested during this ticker's simulation
                results[ticker] = None
                break
            except Exception as e:
                print(f"Failed to simulate {ticker}: {e}")
                results[ticker] = None
        
        # Generate batch report if not stopped
        if simulation_id is None or not self._stop_requested.get(simulation_id, False):
            self._generate_batch_report(results)
        
        # Clean up stop tracking
        if simulation_id is not None and simulation_id in self._stop_requested:
            del self._stop_requested[simulation_id]
            
        return results
    
    def _generate_batch_report(self, results):
        """Generate aggregate report for batch simulation."""
        try:
            from .analysis import generate_batch_report
            report_path = generate_batch_report(results, self._reports_dir)
            print(f"Generated batch report: {report_path}")
            return report_path
        except Exception as e:
            print(f"Warning: Could not generate batch report: {e}")
            return None 