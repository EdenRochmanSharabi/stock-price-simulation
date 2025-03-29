#!/usr/bin/env python3

"""
Geometric Brownian Motion Model
-------------------------------
Implementation of the GBM stock price simulation model.
"""

import numpy as np
from .base_model import StockModel


class GBMModel(StockModel):
    """
    Geometric Brownian Motion model for stock price simulation.
    
    Standard model for stock price movements, based on the formula:
    dS_t = μ*S_t*dt + σ*S_t*dW_t
    
    Implements simulate() method required by the base class.
    """
    
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