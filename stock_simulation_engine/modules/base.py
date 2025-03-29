#!/usr/bin/env python3

"""
Base Simulation Models
----------------------
Base classes and utilities for stock price simulations.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime


class StockModel:
    """Base class for stock price simulation models."""
    
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
        self.ticker = ticker
        self.start_date = start_date if start_date else datetime.now()
        self.lookback_period = lookback_period
        
        # Load historical data and set initial price
        self.historical_data = self._load_historical_data()
        if self.historical_data.empty:
            raise ValueError(f"Could not load historical data for {ticker}")
        
        # Properly extract the last close price as a float
        last_close = self.historical_data['Close'].iloc[-1]
        self.initial_price = float(last_close.iloc[0]) if hasattr(last_close, 'iloc') else float(last_close)
        
        print(f"Initial price for {ticker}: {self.initial_price}")
        
        # Set model parameters
        if calibrate:
            self.mu, self.sigma = self._calibrate_model()
        else:
            self.mu = mu if mu is not None else 0.08  # Default annualized return of 8%
            self.sigma = sigma if sigma is not None else 0.20  # Default annualized volatility of 20%
            
        print(f"Model parameters for {ticker}: mu={self.mu:.4f}, sigma={self.sigma:.4f}")
        
    def _load_historical_data(self):
        """Load historical price data for the ticker."""
        try:
            data = yf.download(
                self.ticker,
                period=self.lookback_period,
                progress=False,
                auto_adjust=True
            )
            return data
        except Exception as e:
            print(f"Error loading data for {self.ticker}: {e}")
            return pd.DataFrame()
    
    def _calibrate_model(self):
        """Calibrate model parameters based on historical data."""
        try:
            # Calculate daily returns
            close_prices = self.historical_data['Close'].values
            returns = np.log(close_prices[1:] / close_prices[:-1])
            
            # Calculate annualized parameters
            days_per_year = 252
            mu_value = returns.mean() * days_per_year
            sigma_value = returns.std() * np.sqrt(days_per_year)
            
            return float(mu_value), float(sigma_value)
        except Exception as e:
            print(f"Error in calibration for {self.ticker}: {e}")
            return 0.08, 0.20  # Default values
    
    def simulate(self, paths=1000, steps=252, dt=1/252):
        """Base simulation method to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement this method")
    
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
            original_initial_price = self.initial_price
            
            # Temporarily set the initial price
            self.initial_price = initial_price
            
            # Simulate a single path
            paths = self.simulate(paths=1, steps=steps, dt=dt)
            
            # Restore the original initial price
            self.initial_price = original_initial_price
            
            # Return the single path without the initial price
            return paths[0, 1:]
        except Exception as e:
            print(f"Error in simulate_path for {self.ticker}: {str(e)}")
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