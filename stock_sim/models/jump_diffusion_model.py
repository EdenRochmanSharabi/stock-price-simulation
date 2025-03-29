#!/usr/bin/env python3

"""
Jump Diffusion Model
-------------------
Implementation of the Jump Diffusion model for stock price simulation.
"""

import numpy as np
from .base_model import StockModel


class JumpDiffusionModel(StockModel):
    """
    Jump diffusion model for stock price simulation.
    
    Extends GBM with jumps to model market shocks using the formula:
    dS_t = μ*S_t*dt + σ*S_t*dW_t + J_t*dN_t
    
    Where:
    - J_t is the jump size
    - N_t is a Poisson process
    """
    
    def __init__(self, ticker, start_date=None, lookback_period="2y",
                 calibrate=True, mu=None, sigma=None, 
                 jump_intensity=10, jump_mean=-0.01, jump_sigma=0.02):
        """
        Initialize the jump diffusion model with jump parameters.
        
        Args:
            ticker (str): Stock ticker symbol
            start_date (datetime, optional): Start date for simulation
            lookback_period (str): Period for historical data to use in calibration
            calibrate (bool): Whether to calibrate the model using historical data
            mu (float, optional): Drift parameter (annualized)
            sigma (float, optional): Volatility parameter (annualized)
            jump_intensity (float): Average number of jumps per year
            jump_mean (float): Mean of jump size distribution
            jump_sigma (float): Standard deviation of jump size distribution
        """
        super().__init__(ticker, start_date, lookback_period, calibrate, mu, sigma)
        
        # Jump parameters with encapsulation
        self._jump_intensity = jump_intensity
        self._jump_mean = jump_mean
        self._jump_sigma = jump_sigma
        
        # Calibrate jump parameters if requested
        if calibrate:
            self._calibrate_jump_parameters()
    
    @property
    def jump_intensity(self):
        """Get the jump intensity parameter."""
        return self._jump_intensity
    
    @property
    def jump_mean(self):
        """Get the jump mean parameter."""
        return self._jump_mean
    
    @property
    def jump_sigma(self):
        """Get the jump sigma parameter."""
        return self._jump_sigma
    
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
            self._jump_intensity = len(potential_jumps) / (len(returns) / days_per_year)
            
            if len(potential_jumps) > 0:
                self._jump_mean = float(potential_jumps.mean())
                self._jump_sigma = float(potential_jumps.std())
            
            print(f"Jump parameters for {self.ticker}:")
            print(f"  Intensity: {self._jump_intensity:.2f} jumps/year")
            print(f"  Mean jump size: {self._jump_mean:.4f}")
            print(f"  Jump volatility: {self._jump_sigma:.4f}")
            
        except Exception as e:
            print(f"Error calibrating jump parameters for {self.ticker}: {e}")
            # Fallback to default parameters
            self._jump_intensity = 10
            self._jump_mean = -0.01
            self._jump_sigma = 0.02
    
    def simulate(self, paths=1000, steps=252, dt=1/252):
        """
        Simulate stock price paths using a Jump Diffusion model.
        
        Args:
            paths (int): Number of simulation paths
            steps (int): Number of time steps
            dt (float): Time step size in years
            
        Returns:
            numpy.ndarray: Array of shape (paths, steps+1) containing simulated paths
        """
        # Initialize price matrix
        price_paths = np.zeros((paths, steps + 1))
        price_paths[:, 0] = self.initial_price
        
        # Generate random normal variates for diffusion
        Z = np.random.normal(0, 1, (paths, steps))
        
        # Jump parameters
        jump_prob = self._jump_intensity * dt  # Probability of a jump in this time step
        
        # Simulate paths
        for t in range(1, steps + 1):
            # Generate jump indicators (Poisson process)
            jump_indicators = np.random.random(paths) < jump_prob
            
            # Generate jump sizes (only for paths with jumps)
            jump_sizes = np.zeros(paths)
            jumps_count = jump_indicators.sum()
            
            if jumps_count > 0:
                jump_sizes[jump_indicators] = np.random.normal(
                    self._jump_mean, self._jump_sigma, size=jumps_count
                )
            
            # GBM formula with jumps
            price_paths[:, t] = price_paths[:, t-1] * np.exp(
                (self.mu - 0.5 * self.sigma**2) * dt + self.sigma * np.sqrt(dt) * Z[:, t-1] + jump_sizes
            )
            
        return price_paths 