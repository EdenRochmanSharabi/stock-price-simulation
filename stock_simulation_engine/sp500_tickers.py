#!/usr/bin/env python3

"""
S&P 500 Tickers Management
-------------------------
Module for managing and retrieving S&P 500 tickers from various sources.
"""

import pandas as pd
import yfinance as yf
import os
from typing import List, Dict, Optional

def get_sp500_from_wikipedia() -> Optional[List[str]]:
    """
    Get S&P 500 tickers from Wikipedia.
    
    Returns:
        List[str]: List of ticker symbols, or None if failed
    """
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        df = pd.read_html(url)[0]
        tickers = df['Symbol'].tolist()
        tickers = [t.replace('.', '-') for t in tickers]  # yfinance uses '-' instead of '.'
        print(f"Retrieved {len(tickers)} tickers from Wikipedia.")
        return sorted(tickers)
    except Exception as e:
        print("Error retrieving from Wikipedia:", e)
        return None

def get_sp500_from_yahoo() -> Optional[List[str]]:
    """
    Get S&P 500 tickers from Yahoo Finance (placeholder for future implementation).
    
    Returns:
        List[str]: List of ticker symbols, or None if failed
    """
    try:
        sp500_etf = yf.Ticker("SPY")
        holdings = sp500_etf.history(period="1d")
        if holdings.empty:
            raise ValueError("SPY has no data, possible error.")
        raise NotImplementedError("Yahoo Finance does not expose constituent tickers via yfinance.")
    except Exception as e:
        print("Error retrieving from Yahoo Finance:", e)
        return None

def get_sp500_tickers() -> List[str]:
    """
    Get S&P 500 tickers from available sources.
    
    Returns:
        List[str]: List of ticker symbols
    
    Raises:
        RuntimeError: If no tickers could be retrieved
    """
    tickers = get_sp500_from_wikipedia()
    if tickers:
        return tickers
    tickers = get_sp500_from_yahoo()
    if tickers:
        return tickers
    raise RuntimeError("Could not retrieve S&P 500 tickers from any source.")

def get_sector_mapping() -> Dict[str, List[str]]:
    """
    Get sector mapping for S&P 500 tickers from Wikipedia.
    
    Returns:
        Dict[str, List[str]]: Dictionary mapping sectors to lists of tickers
    """
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        df = pd.read_html(url)[0]
        
        # Clean tickers
        df['Symbol'] = df['Symbol'].apply(lambda x: x.replace('.', '-'))
        
        # Group by sector
        sector_mapping = {}
        for sector, group in df.groupby('GICS Sector'):
            sector_mapping[sector] = sorted(group['Symbol'].tolist())
        
        print(f"Retrieved sector mapping for {len(df)} tickers across {len(sector_mapping)} sectors.")
        return sector_mapping
    except Exception as e:
        print("Error retrieving sector mapping:", e)
        return {}

def save_tickers_to_csv(tickers: List[str], filename: str = "sp500_tickers.csv") -> None:
    """
    Save tickers to a CSV file.
    
    Args:
        tickers (List[str]): List of ticker symbols
        filename (str): Output filename
    """
    df = pd.DataFrame(tickers, columns=["Ticker"])
    df.to_csv(filename, index=False)
    print(f"Saved {len(tickers)} tickers to {filename}")

def save_sector_mapping_to_csv(sector_mapping: Dict[str, List[str]], 
                             filename: str = "sp500_sectors.csv") -> None:
    """
    Save sector mapping to a CSV file.
    
    Args:
        sector_mapping (Dict[str, List[str]]): Dictionary mapping sectors to tickers
        filename (str): Output filename
    """
    # Convert to DataFrame
    rows = []
    for sector, tickers in sector_mapping.items():
        for ticker in tickers:
            rows.append({"Sector": sector, "Ticker": ticker})
    
    df = pd.DataFrame(rows)
    df.to_csv(filename, index=False)
    print(f"Saved sector mapping for {len(df)} tickers to {filename}")

def load_tickers_from_csv(filename: str = "sp500_tickers.csv") -> List[str]:
    """
    Load tickers from a CSV file.
    
    Args:
        filename (str): Input filename
    
    Returns:
        List[str]: List of ticker symbols
    """
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found, retrieving fresh data...")
        return get_sp500_tickers()
    
    df = pd.read_csv(filename)
    return df["Ticker"].tolist()

def load_sector_mapping_from_csv(filename: str = "sp500_sectors.csv") -> Dict[str, List[str]]:
    """
    Load sector mapping from a CSV file.
    
    Args:
        filename (str): Input filename
    
    Returns:
        Dict[str, List[str]]: Dictionary mapping sectors to tickers
    """
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found, retrieving fresh data...")
        return get_sector_mapping()
    
    try:
        df = pd.read_csv(filename)
        
        # Check if the file structure is correct (expected: Ticker,Sector)
        if "Ticker" in df.columns and "Sector" in df.columns:
            # Group by sector
            sector_mapping = {}
            for _, row in df.iterrows():
                sector = row["Sector"]
                ticker = row["Ticker"]
                if sector not in sector_mapping:
                    sector_mapping[sector] = []
                sector_mapping[sector].append(ticker)
            
            # Sort tickers within each sector
            for sector in sector_mapping:
                sector_mapping[sector].sort()
            
            return sector_mapping
        else:
            print("Warning: CSV file does not have the expected columns. Attempting to group by industry sectors...")
            
            # If the CSV has a different structure, try to determine real sectors
            # Use predefined sectors
            industry_sectors = {
                "Technology": [],
                "Healthcare": [],
                "Financial Services": [],
                "Consumer Discretionary": [],
                "Communication Services": [],
                "Industrials": [],
                "Consumer Staples": [],
                "Energy": [],
                "Utilities": [],
                "Real Estate": [],
                "Materials": [],
                "Other": []  # Default sector
            }
            
            # Assign companies to real sectors based on known mappings
            sector_assignments = {
                "AAPL": "Technology", "MSFT": "Technology", "AMZN": "Consumer Discretionary",
                "GOOGL": "Communication Services", "GOOG": "Communication Services",
                "META": "Communication Services", "TSLA": "Consumer Discretionary",
                "NVDA": "Technology", "BRK-B": "Financial Services", "JPM": "Financial Services",
                "XOM": "Energy", "JNJ": "Healthcare", "PG": "Consumer Staples",
                "V": "Financial Services", "MA": "Financial Services", "BAC": "Financial Services",
                "AVGO": "Technology", "CVX": "Energy", "ABBV": "Healthcare",
                "PEP": "Consumer Staples", "COST": "Consumer Staples", "KO": "Consumer Staples",
                "MRK": "Healthcare", "ADBE": "Technology", "WMT": "Consumer Staples",
                "CRM": "Technology", "TMO": "Healthcare", "MCD": "Consumer Discretionary"
            }
            
            tickers = df["Ticker"].tolist() if "Ticker" in df.columns else []
            
            # If tickers aren't in the expected column, try to find them
            if not tickers and len(df.columns) >= 1:
                tickers = df.iloc[:, 0].tolist()  # Use first column
            
            # Assign tickers to sectors
            for ticker in tickers:
                # Get sector from our predefined mapping, or default to "Other"
                sector = sector_assignments.get(ticker, "Other")
                industry_sectors[sector].append(ticker)
            
            # Return only sectors that have tickers
            return {k: v for k, v in industry_sectors.items() if v}
    except Exception as e:
        print(f"Error loading sector mapping: {e}")
        
        # Create minimal sector mapping as fallback
        sector_mapping = {"S&P 500": []}
        try:
            # Try to at least get the tickers
            tickers = pd.read_csv(filename).iloc[:, 0].tolist()  # First column
            sector_mapping["S&P 500"] = sorted(tickers)
        except:
            print("Could not read tickers from file")
        
        return sector_mapping

if __name__ == "__main__":
    # Example usage
    print("Retrieving S&P 500 tickers...")
    tickers = get_sp500_tickers()
    save_tickers_to_csv(tickers)
    
    print("\nRetrieving sector mapping...")
    sector_mapping = get_sector_mapping()
    save_sector_mapping_to_csv(sector_mapping)
    
    print("\nSummary:")
    for sector, tickers in sector_mapping.items():
        print(f"{sector}: {len(tickers)} tickers") 