#!/usr/bin/env python3

"""
Simulation Engine
----------------
Core simulation engine for running stock price simulations.
"""

import os
import json
import time
from datetime import datetime
from .models import ModelFactory
from typing import Dict, Any, List, Optional, Callable


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
    
    def run_simulation(self, ticker: str, model_config: Dict[str, Any], calibrate: bool = True, simulation_id: Optional[Any] = None):
        """
        Runs a single stock simulation using the provided configuration.

        Args:
            ticker (str): Stock ticker symbol
            model_config (Dict[str, Any]): Dictionary containing simulation parameters:
                - model_type (str): Type of model ('gbm', 'jump', 'hybrid', 'combined')
                - paths (int): Number of simulation paths
                - steps (int): Number of time steps per path
                - dt (float): Time step size (e.g., 1/252 for daily)
                - lookback_period (str): Period for historical data (e.g., "2y")
                - Other model-specific parameters...
            calibrate (bool): Whether to calibrate the model using historical data
            simulation_id (any): Optional ID for tracking simulation status

        Returns:
            dict: Simulation results and statistics

        Raises:
            Exception: If any step of the simulation process fails
            InterruptedError: If the simulation is stopped by the user
        """
        try:
            # Extract parameters from model_config with defaults
            model_type = model_config.get('model_type', 'gbm')
            # Fix for model_type being a dict - ensure it's a string
            if isinstance(model_type, dict) and 'type' in model_type:
                # Handle case where model_type itself is a dictionary with a 'type' key
                model_type = model_type['type']
            # Ensure model_type is a string
            if not isinstance(model_type, str):
                model_type = str(model_type)  # Force conversion to string as last resort
                
            paths = int(model_config.get('paths', 1000))
            steps = int(model_config.get('steps', 21))
            dt = float(model_config.get('dt', 1/252))
            lookback_period = model_config.get('lookback_period', '2y')
            save_full_paths = model_config.get('save_full_paths', False)  # Default to False to save disk space

            # Separate model-specific kwargs from general config
            # Exclude keys already explicitly handled
            known_keys = {'model_type', 'paths', 'steps', 'dt', 'lookback_period', 'save_full_paths'}
            model_specific_kwargs = {k: v for k, v in model_config.items() if k not in known_keys}

            # Reset stop flag if a simulation ID is provided
            if simulation_id is not None:
                self._stop_requested[simulation_id] = False
            
            # --- DEBUGGING START ---
            print(f"[DEBUG ENGINE] Received model_config: {model_config}")
            print(f"[DEBUG ENGINE] Extracted model_type: {model_type} (Type: {type(model_type)})")
            print(f"[DEBUG ENGINE] Extracted model_specific_kwargs: {model_specific_kwargs}")
            if not isinstance(model_type, str):
                 print("[DEBUG ENGINE] ERROR: model_type is NOT a string!")
                 # Optionally raise an error here to halt execution immediately
                 # raise TypeError(f"Expected model_type to be str, but got {type(model_type)}")
            # --- DEBUGGING END ---

            # Create the model using the factory
            try:
                model = ModelFactory.create_model(
                    model_type=model_type, # Pass the extracted model_type string
                    ticker=ticker,
                    lookback_period=lookback_period,
                    calibrate=calibrate,
                    **model_specific_kwargs # Pass other params from config
                )
            except ValueError as e:
                # If we can't load historical data, create a message and raise
                if "Could not load historical data" in str(e):
                    error_msg = f"Error processing {ticker}: {str(e)}"
                    print(error_msg)
                    # Propagate the error but with a cleaner message
                    raise ValueError(error_msg)
                else:
                    # For other ValueErrors, re-raise
                    raise
            
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
            data_path = save_simulation_data(ticker, paths_matrix, statistics, self._data_dir, save_full_paths=save_full_paths)
            
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
                'model_type': model_type, # Use extracted model_type
                'paths_matrix': paths_matrix,
                'statistics': statistics,
                'initial_price': initial_price,
                'model_params': self._get_model_params(model, model_type), # Use extracted model_type
                'data_path': data_path,
                'plot_paths': plot_paths,
                # Add simulation config details to the result for clarity
                'simulation_config': {
                    'paths': paths,
                    'steps': steps,
                    'dt': dt,
                    'lookback_period': lookback_period,
                    'calibrate': calibrate,
                    **model_specific_kwargs
                }
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
        except ValueError as e:
            # For "Could not load historical data" errors, we want to propagate the clean message
            if "Error processing" in str(e):
                raise
            
            # For other ValueError exceptions, add more context
            import traceback
            print(f"Error running simulation for {ticker}: {str(e)}")
            traceback.print_exc()
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
            
            # Create a modified result with the needed structure for the report generator
            report_result = {
                'statistics': result['statistics'].copy(),
                'paths_matrix': result['paths_matrix'],
                'model_type': result['model_type'],
                'model_params': result['model_params']
            }
            
            # Ensure num_paths is set in statistics
            report_result['statistics']['num_paths'] = result['paths_matrix'].shape[0]
            
            # Generate the report
            report_path = generate_stock_report(ticker, report_result, self._reports_dir)
            print(f"Generated report for {ticker}: {report_path}")
            return report_path
            
        except Exception as e:
            import traceback
            print(f"Warning: Could not generate report for {ticker}: {e}")
            traceback.print_exc()
            return None
    
    def batch_simulate(self, tickers: List[str], model_config: Dict[str, Any], simulation_id: Optional[Any] = None, status_callback: Optional[Callable] = None):
        """
        Perform batch simulation for multiple tickers.
        
        Args:
            tickers (List[str]): List of stock ticker symbols
            model_config (Dict[str, Any]): Model configuration parameters
            simulation_id (any): Optional ID for tracking simulation status
            status_callback (Callable): Optional callback for progress updates
            
        Returns:
            dict: Results for each ticker
        """
        results = {}
        
        if not tickers:
            print("No tickers provided for batch simulation")
            return results
        
        total_tickers = len(tickers)
        print(f"Starting batch simulation for {total_tickers} stocks...")
        
        try:
            for i, ticker in enumerate(tickers):
                if simulation_id is not None and self._stop_requested.get(simulation_id, False):
                    print(f"Batch simulation {simulation_id} was stopped by user")
                    raise InterruptedError("Batch simulation was stopped by user")
                
                progress = (i / total_tickers) * 100
                print(f"[{progress:.1f}%] Processing {ticker} ({i+1}/{total_tickers})...")
                
                if status_callback:
                    status_callback(ticker=ticker, status="running", progress=progress)
                
                try:
                    result = self.run_simulation(ticker, model_config, simulation_id=simulation_id)
                    results[ticker] = result
                    if status_callback:
                        status_callback(ticker=ticker, status="completed", progress=progress)
                except ValueError as ve:
                    print(f"Error processing {ticker}: {str(ve)}")
                    if status_callback:
                        status_callback(ticker=ticker, status="error", error=str(ve), progress=progress)
                except Exception as e:
                    print(f"Error processing {ticker}: {str(e)}")
                    if status_callback:
                        status_callback(ticker=ticker, status="error", error=str(e), progress=progress)
            
            # Generate batch report if results exist
            if results:
                self._generate_batch_report(results)
                
                # Clean up raw data files to save disk space
                from .analysis import cleanup_raw_data
                cleanup_raw_data(data_dir=self._data_dir)
                
            return results
            
        except InterruptedError:
            # Still generate batch report for completed simulations
            if results:
                self._generate_batch_report(results)
                
                # Clean up raw data files to save disk space
                from .analysis import cleanup_raw_data
                cleanup_raw_data(data_dir=self._data_dir)
                
            if status_callback:
                status_callback(ticker="batch", status="interrupted", progress=100)
            raise
    
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