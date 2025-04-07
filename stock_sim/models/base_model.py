#!/usr/bin/env python3

"""
Base Simulation Models
----------------------
Base classes and interfaces for stock price simulations.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from abc import ABC, abstractmethod
import time


class StockModel(ABC):
    """
    Abstract base class for stock price simulation models.
    Implements model calibration and data fetching with proper encapsulation.
    """
    
    def __init__(self, ticker, start_date=None, lookback_period="2y",
                 calibrate=True, mu=None, sigma=None):
        """
        Initialize the simulation model.
        
        Args:
            ticker (str): Stock ticker symbol
            start_date (datetime, optional): Start date for simulation
            lookback_period (str): Period for historical data to use in calibration
            calibrate (bool): Whether to calibrate the model using historical data
            mu (float, optional): Drift parameter (annualized)
            sigma (float, optional): Volatility parameter (annualized)
        """
        self._ticker = ticker
        self._start_date = start_date if start_date else datetime.now()
        self._lookback_period = lookback_period
        
        # Load historical data with encapsulation
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            self._historical_data = self._load_historical_data()
            if not self._historical_data.empty:
                break
            
            retry_count += 1
            if retry_count < max_retries:
                print(f"Retrying data fetch for {ticker} (attempt {retry_count+1}/{max_retries})...")
                time.sleep(2)  # Wait before retrying
        
        if self._historical_data.empty:
            # If we still don't have data, use default values
            print(f"WARNING: Using default values for {ticker} after {max_retries} failed attempts")
            self._mu = mu if mu is not None else 0.08
            self._sigma = sigma if sigma is not None else 0.20
            # Use a reasonable default price if none provided
            self._initial_price = 100.0  
            raise ValueError(f"Could not load historical data for {ticker}")
        
        # Extract the last close price as a float
        try:
            last_close = self._historical_data['Close'].iloc[-1]
            self._initial_price = float(last_close.iloc[0]) if hasattr(last_close, 'iloc') else float(last_close)
            print(f"Initial price for {ticker}: {self._initial_price}")
        except Exception as e:
            print(f"Error extracting initial price for {ticker}: {e}")
            self._initial_price = 100.0  # Default value
            print(f"Using default initial price for {ticker}: {self._initial_price}")
        
        # Set model parameters
        if calibrate and not self._historical_data.empty:
            self._mu, self._sigma = self._calibrate_model()
        else:
            self._mu = mu if mu is not None else 0.08  # Default annualized return of 8%
            self._sigma = sigma if sigma is not None else 0.20  # Default annualized volatility of 20%
            
        print(f"Model parameters for {ticker}: mu={self._mu:.4f}, sigma={self._sigma:.4f}")
    
    @property
    def ticker(self):
        """Get the ticker symbol."""
        return self._ticker
    
    @property
    def initial_price(self):
        """Get the initial price."""
        return self._initial_price
    
    @property
    def mu(self):
        """Get the drift parameter."""
        return self._mu
    
    @property
    def sigma(self):
        """Get the volatility parameter."""
        return self._sigma
    
    @property
    def historical_data(self):
        """Get the historical data."""
        return self._historical_data
        
    def _load_historical_data(self):
        """Load historical price data for the ticker."""
        try:
            print(f"Fetching historical data for {self._ticker} with period {self._lookback_period}")
            data = yf.download(
                self._ticker,
                period=self._lookback_period,
                progress=False,
                auto_adjust=True
            )
            if data.empty:
                print(f"WARNING: Empty data returned for {self._ticker}")
            else:
                print(f"Successfully fetched {len(data)} rows for {self._ticker}")
            return data
        except Exception as e:
            print(f"Error loading data for {self._ticker}: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def _calibrate_model(self):
        """Calibrate model parameters based on historical data."""
        try:
            # Calculate daily returns
            close_prices = self._historical_data['Close'].values
            if len(close_prices) < 2:
                print(f"ERROR: Insufficient data for {self._ticker}. Only {len(close_prices)} data points available.")
                return 0.08, 0.20  # Default values
                
            print(f"Calibrating model for {self._ticker} with {len(close_prices)} data points")
            returns = np.log(close_prices[1:] / close_prices[:-1])
            
            # Calculate annualized parameters
            days_per_year = 252
            mu_value = returns.mean() * days_per_year
            sigma_value = returns.std() * np.sqrt(days_per_year)
            
            print(f"Calibration successful for {self._ticker}: mu={mu_value:.4f}, sigma={sigma_value:.4f}")
            return float(mu_value), float(sigma_value)
        except Exception as e:
            print(f"Error in calibration for {self._ticker}: {e}")
            import traceback
            traceback.print_exc()
            return 0.08, 0.20  # Default values
    
    @abstractmethod
    def simulate(self, paths=1000, steps=252, dt=1/252):
        """
        Abstract method to simulate stock price paths.
        
        Args:
            paths (int): Number of simulation paths
            steps (int): Number of time steps
            dt (float): Time step size in years
            
        Returns:
            numpy.ndarray: Array of shape (paths, steps+1) containing simulated paths
        """
        pass
    
    def simulate_path(self, initial_price, steps, dt=None):
        """
        Simulate a single price path.
        
        Args:
            initial_price (float): Initial price
            steps (int): Number of time steps
            dt (float, optional): Time step size in years
            
        Returns:
            numpy.ndarray: Array of length 'steps' containing a simulated path
        """
        try:
            if dt is None:
                dt = 1/252
                
            # Store the original initial price
            original_initial_price = self._initial_price
            
            # Temporarily set the initial price
            self._initial_price = initial_price
            
            # Simulate a single path
            paths = self.simulate(paths=1, steps=steps, dt=dt)
            
            # Restore the original initial price
            self._initial_price = original_initial_price
            
            # Return the single path without the initial price
            return paths[0, 1:]
        except Exception as e:
            print(f"Error in simulate_path for {self._ticker}: {str(e)}")
            # Return a simple path with modest growth as a fallback
            path = np.zeros(steps)
            mu, sigma = 0.08/252, 0.2/np.sqrt(252)  # Default parameters
            for i in range(steps):
                # Simple Geometric Brownian Motion
                path[i] = initial_price * np.exp((mu - 0.5 * sigma**2) * (i+1) + sigma * np.random.normal(0, np.sqrt(i+1)))
            return path


def calculate_returns(prices):
    """Calculate log returns from a price array."""
    return np.log(prices[1:] / prices[:-1]) 