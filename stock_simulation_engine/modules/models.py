#!/usr/bin/env python3

"""
Simulation Models
----------------
Implementation of specific stock price simulation models:
- Geometric Brownian Motion
- Jump Diffusion
- Combined Model (GBM + jumps + volatility clustering)
"""

import numpy as np
from .base import StockModel
from datetime import datetime


class GBMModel(StockModel):
    """Standard Geometric Brownian Motion model for stock price simulation."""
    
    def simulate(self, paths=1000, steps=252, dt=1/252):
        """
        Simulate stock price paths using Geometric Brownian Motion.
        
        Args:
            paths (int): Number of simulation paths
            steps (int): Number of time steps
            dt (float): Time step size in years
            
        Returns:
            numpy.ndarray: Array of shape (paths, steps+1) containing simulated paths
        """
        # Initialize price matrix (each row is a path)
        price_paths = np.zeros((paths, steps + 1))
        price_paths[:, 0] = self.initial_price
        
        # Generate random normal variates
        Z = np.random.normal(0, 1, (paths, steps))
        
        # Simulate paths
        for t in range(1, steps + 1):
            # GBM formula: S_t = S_{t-1} * exp((mu - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z)
            price_paths[:, t] = price_paths[:, t-1] * np.exp(
                (self.mu - 0.5 * self.sigma**2) * dt + self.sigma * np.sqrt(dt) * Z[:, t-1]
            )
            
        return price_paths


class JumpDiffusionModel(StockModel):
    """Jump diffusion model for stock price simulation."""
    
    def __init__(self, ticker, start_date=None, lookback_period="2y",
                 calibrate=True, mu=None, sigma=None, 
                 jump_intensity=10, jump_mean=-0.01, jump_sigma=0.02):
        """Initialize the jump diffusion model."""
        super().__init__(ticker, start_date, lookback_period, calibrate, mu, sigma)
        
        # Jump parameters
        self.jump_intensity = jump_intensity
        self.jump_mean = jump_mean
        self.jump_sigma = jump_sigma
        
        # Calibrate jump parameters if requested
        if calibrate:
            self._calibrate_jump_parameters()
    
    def _calibrate_jump_parameters(self):
        """Calibrate jump parameters based on historical data."""
        try:
            # Get returns
            close_prices = self.historical_data['Close'].values
            returns = np.log(close_prices[1:] / close_prices[:-1])
            
            # Identify potential jumps (returns exceeding 2 standard deviations)
            std_dev = returns.std()
            potential_jumps = returns[abs(returns) > 2 * std_dev]
            
            # Calculate jump parameters
            days_per_year = 252
            self.jump_intensity = len(potential_jumps) / (len(returns) / days_per_year)
            
            if len(potential_jumps) > 0:
                self.jump_mean = float(potential_jumps.mean())
                self.jump_sigma = float(potential_jumps.std())
            
            print(f"Jump parameters for {self.ticker}:")
            print(f"  Intensity: {self.jump_intensity:.2f} jumps/year")
            print(f"  Mean jump size: {self.jump_mean:.4f}")
            print(f"  Jump volatility: {self.jump_sigma:.4f}")
            
        except Exception as e:
            print(f"Error calibrating jump parameters for {self.ticker}: {e}")
            # Fallback to default parameters
            self.jump_intensity = 10
            self.jump_mean = -0.01
            self.jump_sigma = 0.02
    
    def simulate(self, paths=1000, steps=252, dt=1/252):
        """
        Simulate stock price paths using a Jump Diffusion model.
        """
        # Initialize price matrix
        price_paths = np.zeros((paths, steps + 1))
        price_paths[:, 0] = self.initial_price
        
        # Generate random normal variates for diffusion
        Z = np.random.normal(0, 1, (paths, steps))
        
        # Jump parameters
        jump_prob = self.jump_intensity * dt  # Probability of a jump in this time step
        
        # Simulate paths
        for t in range(1, steps + 1):
            # Generate jump indicators (Poisson process)
            jump_indicators = np.random.random(paths) < jump_prob
            
            # Generate jump sizes (only for paths with jumps)
            jump_sizes = np.zeros(paths)
            jumps_count = jump_indicators.sum()
            
            if jumps_count > 0:
                jump_sizes[jump_indicators] = np.random.normal(
                    self.jump_mean, self.jump_sigma, size=jumps_count
                )
            
            # GBM formula with jumps
            price_paths[:, t] = price_paths[:, t-1] * np.exp(
                (self.mu - 0.5 * self.sigma**2) * dt + self.sigma * np.sqrt(dt) * Z[:, t-1] + jump_sizes
            )
            
        return price_paths


class HybridModel(StockModel):
    """Combined model with GBM, jumps, and volatility clustering."""
    
    def __init__(self, ticker, start_date=None, lookback_period="2y", calibrate=True, 
                 mu=None, sigma=None, vol_clustering=0.85, 
                 jump_intensity=10, jump_mean=-0.01, jump_sigma=0.02):
        """Initialize the combined model."""
        super().__init__(ticker, start_date, lookback_period, calibrate, mu, sigma)
        
        # Additional parameters
        self.vol_clustering = vol_clustering
        
        # Initialize jump model with parameters
        self.jump_model = JumpDiffusionModel(
            ticker, start_date, lookback_period, calibrate, 
            mu=mu, sigma=sigma, 
            jump_intensity=jump_intensity, 
            jump_mean=jump_mean, 
            jump_sigma=jump_sigma
        )
        
    def simulate(self, paths=1000, steps=252, dt=1/252):
        """Simulate stock price paths using the combined model."""
        # Initialize price matrix
        price_paths = np.zeros((paths, steps + 1))
        price_paths[:, 0] = self.initial_price
        
        # Generate random normal variates for diffusion
        Z = np.random.normal(0, 1, (paths, steps))
        
        # Initial volatility is the calibrated sigma
        vol = np.ones(paths) * self.sigma
        
        # Jump parameters
        jump_prob = self.jump_model.jump_intensity * dt
        
        # Simulate paths
        for t in range(1, steps + 1):
            # Volatility clustering - GARCH-like effect
            vol_shock = np.random.normal(0, 0.05, paths)
            vol = self.vol_clustering * vol + (1 - self.vol_clustering) * self.sigma + vol_shock
            vol = np.maximum(vol, 0.05)  # Ensure minimum volatility
            
            # Generate jump indicators and sizes
            jump_indicators = np.random.random(paths) < jump_prob
            jump_sizes = np.zeros(paths)
            jumps_count = jump_indicators.sum()
            
            if jumps_count > 0:
                jump_sizes[jump_indicators] = np.random.normal(
                    self.jump_model.jump_mean, 
                    self.jump_model.jump_sigma, 
                    size=jumps_count
                )
            
            # Combined model formula
            price_paths[:, t] = price_paths[:, t-1] * np.exp(
                (self.mu - 0.5 * vol**2) * dt + vol * np.sqrt(dt) * Z[:, t-1] + jump_sizes
            )
            
        return price_paths 