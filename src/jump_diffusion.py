"""
Module for implementing jump diffusion model for stock price simulation.
"""
import numpy as np
from numba import jit

class JumpDiffusionModel:
    """
    A model for simulating stock price jumps in addition to continuous diffusion.
    
    Uses a Poisson process to model the occurrence of jumps and 
    a log-normal distribution to model jump sizes.
    """
    
    def __init__(self, lambda_=0.1, mu_j=-0.05, sigma_j=0.1):
        """
        Initialize the jump diffusion model.
        
        Parameters:
        -----------
        lambda_ : float, optional
            Jump intensity (average number of jumps per year) (default: 0.1)
        mu_j : float, optional
            Mean of the log-jump size distribution (default: -0.05)
        sigma_j : float, optional
            Standard deviation of the log-jump size distribution (default: 0.1)
        """
        self.lambda_ = lambda_
        self.mu_j = mu_j
        self.sigma_j = sigma_j
        
        # Initialize jump history
        self.jump_times = []
        self.jump_sizes = []
        
    def generate_jump(self, dt):
        """
        Generate a jump for a given time step.
        
        Parameters:
        -----------
        dt : float
            Time step in years
            
        Returns:
        --------
        tuple
            (jump_occurs, jump_size)
            - jump_occurs: bool, whether a jump occurs in this time step
            - jump_size: float, size of the jump (as a factor, e.g., 0.1 for 10% up)
        """
        # Probability of a jump in this time step
        p_jump = 1 - np.exp(-self.lambda_ * dt)
        
        # Determine if a jump occurs
        jump_occurs = np.random.random() < p_jump
        
        if jump_occurs:
            # Generate jump size from log-normal distribution
            jump_size = np.exp(self.mu_j + self.sigma_j * np.random.normal()) - 1
            
            # Update jump history
            self.jump_times.append(len(self.jump_times))
            self.jump_sizes.append(jump_size)
            
            return True, jump_size
        else:
            return False, 0.0
        
    def reset(self):
        """
        Reset the jump history.
        """
        self.jump_times = []
        self.jump_sizes = []

@jit(nopython=True)
def generate_jump_diffusion_path(n_steps, dt, lambda_, mu_j, sigma_j):
    """
    Generate jump indicators and sizes for the entire path.
    
    Parameters:
    -----------
    n_steps : int
        Number of time steps
    dt : float
        Time step size in years
    lambda_ : float
        Jump intensity (average number of jumps per year)
    mu_j : float
        Mean of the log-jump size distribution
    sigma_j : float
        Standard deviation of the log-jump size distribution
        
    Returns:
    --------
    tuple
        (jump_indicators, jump_sizes)
        - jump_indicators: numpy.ndarray, boolean array indicating if a jump occurs
        - jump_sizes: numpy.ndarray, array of jump sizes (0 if no jump)
    """
    # Calculate probability of jump in each time step
    p_jump = 1 - np.exp(-lambda_ * dt)
    
    # Generate jump indicators
    jump_indicators = np.random.random(n_steps) < p_jump
    
    # Generate jump sizes (0 if no jump)
    jump_sizes = np.zeros(n_steps)
    
    # Generate jump sizes for times when jumps occur
    for i in range(n_steps):
        if jump_indicators[i]:
            jump_sizes[i] = np.exp(mu_j + sigma_j * np.random.normal()) - 1
            
    return jump_indicators, jump_sizes

@jit(nopython=True)
def apply_jumps_to_path(stock_prices, jump_indicators, jump_sizes):
    """
    Apply jumps to a stock price path.
    
    Parameters:
    -----------
    stock_prices : numpy.ndarray
        Array of stock prices
    jump_indicators : numpy.ndarray
        Boolean array indicating if a jump occurs at each time step
    jump_sizes : numpy.ndarray
        Array of jump sizes (multiplicative factors)
        
    Returns:
    --------
    numpy.ndarray
        Updated stock prices with jumps applied
    """
    # Create a copy of the stock prices
    updated_prices = stock_prices.copy()
    
    # Apply jumps
    for i in range(len(stock_prices)):
        if jump_indicators[i]:
            # Apply jump as a multiplicative factor
            updated_prices[i] *= (1 + jump_sizes[i])
            
    return updated_prices

def calibrate_jump_parameters(returns, dt=1/252):
    """
    Calibrate jump parameters from historical returns.
    
    This is a simplified method that assumes extreme returns are due to jumps.
    More sophisticated methods would involve maximum likelihood estimation.
    
    Parameters:
    -----------
    returns : numpy.ndarray
        Array of historical returns
    dt : float, optional
        Time step in years (default: 1/252 for daily data)
        
    Returns:
    --------
    tuple
        (lambda_, mu_j, sigma_j)
        - lambda_: Estimated jump intensity
        - mu_j: Estimated mean jump size
        - sigma_j: Estimated jump size volatility
    """
    # Define threshold for jump detection (e.g., 3 standard deviations)
    threshold = 3 * np.std(returns)
    
    # Identify potential jumps (large returns)
    jump_indices = np.where(np.abs(returns) > threshold)[0]
    jump_returns = returns[jump_indices]
    
    if len(jump_returns) == 0:
        # No jumps detected, return default parameters
        return 0.1, -0.05, 0.1
    
    # Estimate lambda (jumps per year)
    lambda_ = len(jump_returns) / (len(returns) * dt)
    
    # Estimate jump size parameters
    # For log-normal jumps, we need to convert returns to ln(1 + return)
    log_jump_sizes = np.log(1 + jump_returns)
    
    mu_j = np.mean(log_jump_sizes)
    sigma_j = np.std(log_jump_sizes)
    
    return lambda_, mu_j, sigma_j 