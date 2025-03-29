#!/usr/bin/env python3

"""
Hybrid Model with Regime Switching
---------------------------------
Implementation of a combined model with GBM, jumps, and volatility clustering.
"""

import numpy as np
from .base_model import StockModel
from .jump_diffusion_model import JumpDiffusionModel


class HybridModel(StockModel):
    """
    Combined model with GBM, jumps, and volatility regime switching.
    
    This model combines:
    1. Geometric Brownian Motion
    2. Jump diffusion for market shocks
    3. Volatility clustering for regime switching
    
    Formula: 
    dS_t = μ*S_t*dt + σ_t*S_t*dW_t + J_t*dN_t
    
    Where σ_t follows a regime-switching process.
    """
    
    def __init__(self, ticker, start_date=None, lookback_period="2y", calibrate=True, 
                 mu=None, sigma=None, vol_clustering=0.85, 
                 jump_intensity=10, jump_mean=-0.01, jump_sigma=0.02):
        """
        Initialize the combined model.
        
        Args:
            ticker (str): Stock ticker symbol
            start_date (datetime, optional): Start date for simulation
            lookback_period (str): Period for historical data
            calibrate (bool): Whether to calibrate model from historical data
            mu (float, optional): Drift parameter (annualized)
            sigma (float, optional): Volatility parameter (annualized)
            vol_clustering (float): Volatility clustering parameter (0-1)
            jump_intensity (float): Average number of jumps per year
            jump_mean (float): Mean of jump size distribution
            jump_sigma (float): Standard deviation of jump size distribution
        """
        super().__init__(ticker, start_date, lookback_period, calibrate, mu, sigma)
        
        # Additional parameters with encapsulation
        self._vol_clustering = vol_clustering
        
        # Create jump model with composition (prefer composition over inheritance)
        self._jump_model = JumpDiffusionModel(
            ticker, start_date, lookback_period, calibrate, 
            mu=mu, sigma=sigma, 
            jump_intensity=jump_intensity, 
            jump_mean=jump_mean, 
            jump_sigma=jump_sigma
        )
    
    @property
    def vol_clustering(self):
        """Get the volatility clustering parameter."""
        return self._vol_clustering
    
    @property
    def jump_model(self):
        """Get the underlying jump diffusion model."""
        return self._jump_model
    
    def simulate(self, paths=1000, steps=252, dt=1/252):
        """
        Simulate stock price paths using the combined model.
        
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
        
        # Initial volatility is the calibrated sigma
        vol = np.ones(paths) * self.sigma
        
        # Jump parameters
        jump_prob = self._jump_model.jump_intensity * dt
        
        # Simulate paths
        for t in range(1, steps + 1):
            # Volatility clustering - GARCH-like effect
            vol_shock = np.random.normal(0, 0.05, paths)
            vol = self._vol_clustering * vol + (1 - self._vol_clustering) * self.sigma + vol_shock
            vol = np.maximum(vol, 0.05)  # Ensure minimum volatility
            
            # Generate jump indicators and sizes
            jump_indicators = np.random.random(paths) < jump_prob
            jump_sizes = np.zeros(paths)
            jumps_count = jump_indicators.sum()
            
            if jumps_count > 0:
                jump_sizes[jump_indicators] = np.random.normal(
                    self._jump_model.jump_mean, 
                    self._jump_model.jump_sigma, 
                    size=jumps_count
                )
            
            # Combined model formula
            price_paths[:, t] = price_paths[:, t-1] * np.exp(
                (self.mu - 0.5 * vol**2) * dt + vol * np.sqrt(dt) * Z[:, t-1] + jump_sizes
            )
            
        return price_paths 