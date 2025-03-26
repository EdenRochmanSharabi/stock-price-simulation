"""
Module for implementing earnings announcement shocks for stock price simulation.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

class EarningsShockModel:
    """
    A model for simulating stock price shocks due to earnings announcements.
    """
    
    def __init__(self, earnings_dates=None, shock_mean=0.0, shock_std=0.05, 
                 pre_earnings_drift=0.01, date_tolerance=2):
        """
        Initialize the earnings shock model.
        
        Parameters:
        -----------
        earnings_dates : list or pd.DatetimeIndex, optional
            List of earnings announcement dates
        shock_mean : float, optional
            Mean of the earnings shock distribution (default: 0.0)
        shock_std : float, optional
            Standard deviation of the earnings shock distribution (default: 0.05)
        pre_earnings_drift : float, optional
            Drift adjustment prior to earnings (default: 0.01)
        date_tolerance : int, optional
            Number of days before and after earnings date to consider (default: 2)
        """
        self.earnings_dates = earnings_dates if earnings_dates is not None else []
        self.shock_mean = shock_mean
        self.shock_std = shock_std
        self.pre_earnings_drift = pre_earnings_drift
        self.date_tolerance = date_tolerance
        
        # Initialize shock history
        self.shock_history = []
        
    def is_earnings_day(self, date):
        """
        Check if a given date is an earnings announcement date.
        
        Parameters:
        -----------
        date : datetime.datetime or pd.Timestamp
            Date to check
            
        Returns:
        --------
        bool
            True if date is an earnings date (within tolerance), False otherwise
        """
        if not self.earnings_dates:
            return False
            
        # Convert date to pandas Timestamp for consistent comparison
        date = pd.Timestamp(date)
        
        # Check if date is within tolerance of any earnings date
        for earnings_date in self.earnings_dates:
            earnings_date = pd.Timestamp(earnings_date)
            date_diff = abs((date - earnings_date).days)
            
            if date_diff <= self.date_tolerance:
                return True
                
        return False
        
    def is_pre_earnings_day(self, date, lookforward_days=5):
        """
        Check if a given date is in the pre-earnings period.
        
        Parameters:
        -----------
        date : datetime.datetime or pd.Timestamp
            Date to check
        lookforward_days : int, optional
            Number of days to look forward for earnings (default: 5)
            
        Returns:
        --------
        bool
            True if date is in pre-earnings period, False otherwise
        """
        if not self.earnings_dates:
            return False
            
        # Convert date to pandas Timestamp for consistent comparison
        date = pd.Timestamp(date)
        
        # Check if any earnings date is within the lookforward period
        for earnings_date in self.earnings_dates:
            earnings_date = pd.Timestamp(earnings_date)
            date_diff = (earnings_date - date).days
            
            if 0 < date_diff <= lookforward_days:
                return True
                
        return False
        
    def generate_shock(self, date=None):
        """
        Generate an earnings shock for a given date.
        
        Parameters:
        -----------
        date : datetime.datetime, pd.Timestamp, or None, optional
            Date for which to generate a shock
            If None, simply checks if shock should be generated
            
        Returns:
        --------
        tuple
            (shock_occurs, shock_size)
            - shock_occurs: bool, whether a shock occurs
            - shock_size: float, size of the shock (as a factor, e.g., 0.1 for 10% up)
        """
        # If no date provided, just check if shock should be generated
        if date is None:
            shock_occurs = np.random.random() < 0.01  # 1% chance on any day
        else:
            shock_occurs = self.is_earnings_day(date)
            
        if shock_occurs:
            # Generate shock size from normal distribution
            shock_size = np.random.normal(self.shock_mean, self.shock_std)
            
            # Update shock history
            self.shock_history.append((date, shock_size))
            
            return True, shock_size
        else:
            return False, 0.0
            
    def get_pre_earnings_drift_adjustment(self, date=None):
        """
        Get drift adjustment for pre-earnings period.
        
        Parameters:
        -----------
        date : datetime.datetime, pd.Timestamp, or None, optional
            Date for which to check pre-earnings drift
            
        Returns:
        --------
        float
            Drift adjustment factor
        """
        if date is None:
            return 0.0
            
        if self.is_pre_earnings_day(date):
            return self.pre_earnings_drift
        else:
            return 0.0
            
    def reset(self):
        """
        Reset the shock history.
        """
        self.shock_history = []

def apply_earnings_shocks_to_path(stock_prices, dates, earnings_dates, 
                                 shock_mean=0.0, shock_std=0.05, date_tolerance=2):
    """
    Apply earnings shocks to a stock price path.
    
    Parameters:
    -----------
    stock_prices : numpy.ndarray
        Array of stock prices
    dates : list or array-like
        Dates corresponding to stock prices
    earnings_dates : list or array-like
        Earnings announcement dates
    shock_mean : float, optional
        Mean of the earnings shock distribution (default: 0.0)
    shock_std : float, optional
        Standard deviation of the earnings shock distribution (default: 0.05)
    date_tolerance : int, optional
        Number of days before and after earnings date to consider (default: 2)
        
    Returns:
    --------
    numpy.ndarray
        Updated stock prices with earnings shocks applied
    list
        List of shock events (date, index, shock_size)
    """
    # Create a copy of the stock prices
    updated_prices = stock_prices.copy()
    shock_events = []
    
    # Convert dates and earnings_dates to pandas DatetimeIndex for consistent comparison
    dates = pd.DatetimeIndex(dates)
    earnings_dates = [pd.Timestamp(date) for date in earnings_dates]
    
    # Check each date for earnings announcements
    for i, date in enumerate(dates):
        for earnings_date in earnings_dates:
            date_diff = abs((date - earnings_date).days)
            
            if date_diff <= date_tolerance:
                # Generate a shock for this earnings announcement
                shock_size = np.random.normal(shock_mean, shock_std)
                
                # Apply shock to stock price
                updated_prices[i] *= (1 + shock_size)
                
                # Record the shock event
                shock_events.append((date, i, shock_size))
                
                break  # Only apply one shock per date
    
    return updated_prices, shock_events

def estimate_earnings_shock_parameters(stock_data, earnings_dates, window=3):
    """
    Estimate earnings shock parameters from historical data.
    
    Parameters:
    -----------
    stock_data : pandas.DataFrame
        DataFrame with stock price data
    earnings_dates : list or array-like
        Earnings announcement dates
    window : int, optional
        Number of days around earnings date to consider (default: 3)
        
    Returns:
    --------
    tuple
        (shock_mean, shock_std)
        - shock_mean: Estimated mean earnings shock
        - shock_std: Estimated standard deviation of earnings shocks
    """
    # Calculate daily returns
    returns = stock_data['Adj Close'].pct_change().dropna()
    
    # Convert index to DatetimeIndex if it's not already
    if not isinstance(returns.index, pd.DatetimeIndex):
        returns.index = pd.DatetimeIndex(returns.index)
    
    # Convert earnings_dates to pandas Timestamps
    earnings_dates = [pd.Timestamp(date) for date in earnings_dates]
    
    # Collect returns around earnings dates
    earnings_returns = []
    
    for earnings_date in earnings_dates:
        for day_offset in range(-window, window+1):
            target_date = earnings_date + pd.Timedelta(days=day_offset)
            
            if target_date in returns.index:
                earnings_returns.append(returns.loc[target_date])
    
    if not earnings_returns:
        # No returns found around earnings dates
        return 0.0, 0.05  # Default values
    
    # Calculate statistics of earnings returns
    shock_mean = np.mean(earnings_returns)
    shock_std = np.std(earnings_returns)
    
    return shock_mean, shock_std 