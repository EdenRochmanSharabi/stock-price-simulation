"""
Strategy Executor Module
-----------------------
Handles execution of user-defined trading strategies and comparison with the model.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any
import yfinance as yf
from datetime import datetime
import traceback
import sys
from io import StringIO
import contextlib
import ast
import re

class StrategyExecutor:
    # Class-level forbidden imports list
    FORBIDDEN_IMPORTS = {
        'os', 'sys', 'subprocess', 'shutil', 'socket', 'http', 'urllib', 'requests',
        'multiprocessing', 'threading', 'ctypes', 'cffi', 'pickle', 'marshal',
        'importlib', 'import', '__import__', 'eval', 'exec', 'compile', 'open',
        'file', 'input', 'raw_input', 'print', 'exit', 'quit', 'globals', 'locals'
    }

    def __init__(self):
        self.available_modules = {
            'numpy': np,
            'pandas': pd,
            'yfinance': yf
        }

    def _calculate_metrics(self, portfolio_values: np.ndarray, risk_free_rate: float = 0.02) -> Dict[str, float]:
        """Calculate performance metrics for a strategy."""
        if len(portfolio_values) < 2:
            return {
                'return': 0.0,
                'sharpe': 0.0,
                'max_drawdown': 0.0
            }

        # Calculate returns
        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        total_return = (portfolio_values[-1] / portfolio_values[0]) - 1

        # Calculate Sharpe ratio (annualized)
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        sharpe = np.sqrt(252) * np.mean(excess_returns) / np.std(returns) if np.std(returns) > 0 else 0

        # Calculate maximum drawdown
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (peak - portfolio_values) / peak
        max_drawdown = np.max(drawdown)

        return {
            'return': total_return,
            'sharpe': sharpe,
            'max_drawdown': max_drawdown
        }

    def execute_strategy(self, code: str, start_date: str, end_date: str, 
                        initial_capital: float, tickers: List[str]) -> Dict[str, Any]:
        """
        Execute a user-defined strategy and compare it with the model.
        
        Args:
            code: Python code string containing the strategy
            start_date: Start date for backtesting
            end_date: End date for backtesting
            initial_capital: Initial capital to invest
            tickers: List of tickers to trade
            
        Returns:
            Dictionary containing strategy results and model comparison
        """
        try:
            # Check for forbidden imports
            forbidden_imports = self._check_forbidden_imports(code)
            if forbidden_imports:
                raise ValueError(f"Forbidden imports detected: {', '.join(forbidden_imports)}")

            # Fetch historical data
            prices = {}
            dates = None
            failed_tickers = []
            
            for ticker in tickers:
                try:
                    data = yf.download(ticker, start=start_date, end=end_date)
                    if data.empty or len(data) == 0:
                        print(f"WARNING: No data available for ticker {ticker} in the specified date range")
                        failed_tickers.append(ticker)
                        continue
                    
                    # Try to get Adj Close, fall back to Close if not available
                    if 'Adj Close' in data.columns:
                        price_data = data['Adj Close']
                    else:
                        price_data = data['Close']
                        
                    # Ensure price data is a 1D array
                    price_array = np.array(price_data.values).flatten()
                    prices[ticker] = price_array
                    print(f"DEBUG: {ticker} price data shape: {price_array.shape}, type: {type(price_array)}, sample: {price_array[:5]}")
                    
                    if dates is None:
                        dates = data.index
                except Exception as e:
                    print(f"ERROR: Failed to fetch data for {ticker}: {str(e)}")
                    failed_tickers.append(ticker)
            
            # Check if we have any valid data
            if len(prices) == 0:
                # All tickers failed - provide sample data for SPY as fallback
                print(f"WARNING: Could not fetch data for any of the tickers: {', '.join(failed_tickers)}")
                print("Using sample SPY data as fallback to allow testing")
                
                # Generate sample data (approximate SPY movement)
                n_days = 252  # Approximately 1 year of trading days
                dates = pd.date_range(start=start_date, periods=n_days)
                
                # Create synthetic SPY-like data: starting at ~$400 with realistic volatility
                base_price = 400.0
                daily_returns = np.random.normal(0.0003, 0.01, n_days)  # Mean daily return and volatility similar to SPY
                
                # Convert returns to prices
                price_array = np.zeros(n_days)
                price_array[0] = base_price
                for i in range(1, n_days):
                    price_array[i] = price_array[i-1] * (1 + daily_returns[i])
                
                # Add the synthetic data
                sample_ticker = "SPY_SAMPLE"
                prices[sample_ticker] = price_array
                print(f"Created sample data with {n_days} days of trading, starting at ${base_price:.2f}")
                
                # Use synthetic dates
                dates = dates
            elif failed_tickers:
                print(f"WARNING: Ignoring tickers with no data: {', '.join(failed_tickers)}")
            
            # Check if dates is valid using the proper approach for DatetimeIndex
            if dates is None or len(dates) == 0:
                raise ValueError("No data available for the specified date range")

            # Create a safe execution environment
            local_dict = {
                'np': np,
                'pd': pd,
                'prices': {ticker: np.array(price_array).flatten() for ticker, price_array in prices.items()},
                'dates': dates.values,
                'initial_capital': initial_capital
            }

            # Execute the strategy code
            output = StringIO()
            with contextlib.redirect_stdout(output):
                try:
                    exec(code, local_dict)
                except Exception as e:
                    raise ValueError(f"Error executing strategy code: {str(e)}")
            
            # Get strategy results
            if 'my_strategy' not in local_dict:
                raise ValueError("Strategy code must define a function named 'my_strategy'")
                
            try:
                strategy_results = local_dict.get('my_strategy')(prices, dates.values, initial_capital)
            except Exception as e:
                raise ValueError(f"Error running strategy function: {str(e)}")
            
            if not isinstance(strategy_results, dict):
                raise ValueError("Strategy must return a dictionary")

            required_keys = {'portfolio_value', 'positions', 'trades'}
            if not all(key in strategy_results for key in required_keys):
                raise ValueError(f"Strategy results must contain all required keys: {required_keys}")

            # Calculate strategy metrics
            portfolio_value = np.array(strategy_results['portfolio_value'])
            strategy_metrics = self._calculate_metrics(portfolio_value)

            # Run model simulation for comparison
            model_results = self._run_model_simulation(tickers, start_date, end_date, initial_capital)
            model_metrics = self._calculate_metrics(model_results['portfolio_value'])
            
            # Ensure that the dates and model_portfolio_value arrays have the same length as portfolio_value
            # This is needed when model simulation returned a default/dummy result
            dates_list = dates.strftime('%Y-%m-%d').tolist()
            model_portfolio_value = model_results['portfolio_value'].tolist()
            
            # If model data is shorter than strategy data, pad it
            if len(model_portfolio_value) < len(portfolio_value):
                model_portfolio_value = model_portfolio_value + [model_portfolio_value[-1]] * (len(portfolio_value) - len(model_portfolio_value))
            
            # If model data is longer than strategy data, truncate it
            if len(model_portfolio_value) > len(portfolio_value):
                model_portfolio_value = model_portfolio_value[:len(portfolio_value)]
            
            # Create normalized trajectories for each individual ticker
            ticker_trajectories = {}
            for ticker in prices.keys():
                # Normalize the ticker's price to start at initial_capital for comparison
                price_data = prices[ticker]
                ticker_trajectory = initial_capital * (price_data / price_data[0])
                # Make sure the trajectory has the same length as portfolio_value
                if len(ticker_trajectory) > len(portfolio_value):
                    ticker_trajectory = ticker_trajectory[:len(portfolio_value)]
                elif len(ticker_trajectory) < len(portfolio_value):
                    # Pad with the last value
                    ticker_trajectory = np.append(ticker_trajectory, 
                                                 np.full(len(portfolio_value) - len(ticker_trajectory), 
                                                         ticker_trajectory[-1]))
                ticker_trajectories[ticker] = ticker_trajectory.tolist()
            
            return {
                'dates': dates_list,
                'portfolio_value': portfolio_value.tolist(),
                'model_portfolio_value': model_portfolio_value,
                'strategy_return': strategy_metrics['return'],
                'strategy_sharpe': strategy_metrics['sharpe'],
                'strategy_max_drawdown': strategy_metrics['max_drawdown'],
                'model_return': model_metrics['return'],
                'model_sharpe': model_metrics['sharpe'],
                'model_max_drawdown': model_metrics['max_drawdown'],
                'model_name': 'Buy & Hold',
                'ticker_trajectories': ticker_trajectories
            }

        except Exception as e:
            error_msg = f"Error executing strategy: {str(e)}\n{traceback.format_exc()}"
            raise RuntimeError(error_msg)

    def _check_forbidden_imports(self, code: str) -> List[str]:
        """Check for forbidden imports in the code."""
        found_imports = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for name in node.names:
                        if name.name in self.FORBIDDEN_IMPORTS:
                            found_imports.append(name.name)
        except SyntaxError:
            # If there's a syntax error, try a more basic check
            for imp in self.FORBIDDEN_IMPORTS:
                if re.search(rf'\b{imp}\b', code):
                    found_imports.append(imp)
        return found_imports

    def _run_model_simulation(self, tickers: List[str], start_date: str, 
                            end_date: str, initial_capital: float) -> Dict[str, Any]:
        """Run the model simulation for comparison."""
        # For now, return a simple buy-and-hold strategy
        ticker = tickers[0]  # Use the first ticker for comparison
        
        try:
            data = yf.download(ticker, start=start_date, end=end_date)
            
            if data.empty:
                # Handle the case when no data is available
                # Return a default/dummy result
                return {
                    'portfolio_value': np.array([initial_capital]),
                    'positions': {ticker: np.array([0])},
                    'trades': []
                }
            
            # Try to get Adj Close, fall back to Close if not available
            if 'Adj Close' in data.columns:
                price_data = data['Adj Close']
            else:
                price_data = data['Close']
            
            # Ensure price data is a 1D array
            price_values = np.array(price_data.values).flatten()
            
            # Calculate portfolio value assuming buy and hold
            shares = initial_capital / price_values[0]
            portfolio_value = shares * price_values
            
            return {
                'portfolio_value': portfolio_value,
                'positions': {ticker: np.full(len(price_values), shares)},
                'trades': []
            }
        except Exception as e:
            # Handle any download or processing errors
            # Return a default/dummy result
            print(f"Error in model simulation: {str(e)}")
            return {
                'portfolio_value': np.array([initial_capital]),
                'positions': {ticker: np.array([0])},
                'trades': []
            } 