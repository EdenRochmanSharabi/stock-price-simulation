"""
Module for retrieving historical stock data using yfinance.
"""
import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def fetch_stock_data(ticker, period="1y", interval="1d", save_to_file=True, data_dir="../data"):
    """
    Fetch historical stock data for a given ticker.
    
    Parameters:
    -----------
    ticker : str
        Stock ticker symbol (e.g., 'AAPL', 'MSFT')
    period : str, optional
        Period of data to download (default: '1y')
    interval : str, optional
        Data interval (default: '1d')
    save_to_file : bool, optional
        Whether to save the data to a CSV file (default: True)
    data_dir : str, optional
        Directory to save the data (default: '../data')
        
    Returns:
    --------
    pandas.DataFrame
        Historical stock data
    """
    try:
        # Create data directory if it doesn't exist
        if save_to_file and not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        # Download stock data
        stock_data = yf.download(ticker, period=period, interval=interval)
        
        if stock_data.empty:
            raise ValueError(f"No data found for ticker: {ticker}")
            
        # Save data to file if requested
        if save_to_file:
            file_path = os.path.join(data_dir, f"{ticker}_data.csv")
            stock_data.to_csv(file_path)
            print(f"Data saved to {file_path}")
            
        return stock_data
    
    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return None

def calculate_volatility(stock_data, window=30, annualize=True, trading_days=252):
    """
    Calculate historical volatility from stock price data.
    
    Parameters:
    -----------
    stock_data : pandas.DataFrame
        Historical stock data with 'Adj Close' column
    window : int, optional
        Rolling window in days for volatility calculation (default: 30)
    annualize : bool, optional
        Whether to annualize the volatility (default: True)
    trading_days : int, optional
        Number of trading days in a year (default: 252)
        
    Returns:
    --------
    pandas.Series
        Historical volatility series
    float
        Average volatility over the period
    """
    # Calculate daily returns
    returns = stock_data['Adj Close'].pct_change().dropna()
    
    # Calculate rolling standard deviation
    rolling_std = returns.rolling(window=window).std()
    
    # Annualize if requested
    if annualize:
        rolling_std = rolling_std * np.sqrt(trading_days)
    
    # Calculate average volatility over the period
    avg_volatility = rolling_std.mean()
    
    return rolling_std, avg_volatility

def get_latest_price(ticker):
    """
    Get the latest price for a stock.
    
    Parameters:
    -----------
    ticker : str
        Stock ticker symbol
        
    Returns:
    --------
    float
        Latest price
    """
    try:
        stock = yf.Ticker(ticker)
        latest_data = stock.history(period="1d")
        
        if latest_data.empty:
            raise ValueError(f"No data found for ticker: {ticker}")
            
        return latest_data['Close'].iloc[-1]
    
    except Exception as e:
        print(f"Error getting latest price for {ticker}: {str(e)}")
        return None

def get_earnings_dates(ticker, future_only=True, n_quarters=4):
    """
    Get past and/or future earnings announcement dates.
    
    Parameters:
    -----------
    ticker : str
        Stock ticker symbol
    future_only : bool, optional
        Whether to return only future earnings dates (default: True)
    n_quarters : int, optional
        Number of quarters to look ahead/behind (default: 4)
        
    Returns:
    --------
    list
        List of earnings announcement dates
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Get earnings calendar information
        earnings_calendar = stock.calendar
        
        if earnings_calendar is None or len(earnings_calendar) == 0:
            # If no future dates available, estimate based on past earnings
            earnings_dates = stock.earnings_dates
            
            if earnings_dates is None or earnings_dates.empty:
                print(f"No earnings data available for {ticker}")
                return []
            
            # Sort dates and get the most recent ones
            earnings_dates = earnings_dates.index.sort_values(ascending=False)
            
            today = pd.Timestamp.today()
            
            if future_only:
                # Filter for future dates only
                earnings_dates = [date for date in earnings_dates if date > today]
            
            # Limit to n_quarters
            earnings_dates = earnings_dates[:n_quarters]
            
            return list(earnings_dates)
        else:
            # Extract earnings date from calendar
            earnings_date = earnings_calendar.get('Earnings Date', None)
            
            if earnings_date:
                return [earnings_date]
            else:
                return []
    
    except Exception as e:
        print(f"Error getting earnings dates for {ticker}: {str(e)}")
        return []

def get_market_parameters(ticker, period="1y"):
    """
    Get key market parameters for simulation.
    
    Parameters:
    -----------
    ticker : str
        Stock ticker symbol
    period : str, optional
        Period for data retrieval (default: '1y')
        
    Returns:
    --------
    dict
        Dictionary containing initial price, volatility, and other parameters
    """
    try:
        # Fetch historical data
        stock_data = fetch_stock_data(ticker, period=period)
        
        if stock_data is None or stock_data.empty:
            raise ValueError(f"No data available for {ticker}")
        
        # Calculate volatility
        _, volatility = calculate_volatility(stock_data)
        
        # Get latest price
        latest_price = stock_data['Adj Close'].iloc[-1]
        
        # Calculate daily returns for drift estimation
        returns = stock_data['Adj Close'].pct_change().dropna()
        drift = returns.mean() * 252  # Annualized drift
        
        # Get earnings dates
        earnings_dates = get_earnings_dates(ticker)
        
        return {
            'ticker': ticker,
            'initial_price': latest_price,
            'volatility': volatility,
            'drift': drift,
            'earnings_dates': earnings_dates,
            'data_start_date': stock_data.index[0],
            'data_end_date': stock_data.index[-1]
        }
    
    except Exception as e:
        print(f"Error calculating market parameters for {ticker}: {str(e)}")
        return None 