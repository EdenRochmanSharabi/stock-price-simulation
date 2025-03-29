#!/usr/bin/env python3

"""
S&P 500 Utilities
---------------
Utilities for working with S&P 500 tickers and sectors.
"""

import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time


class SP500TickerManager:
    """
    Manager for S&P 500 tickers and sector classifications.
    
    Implements data retrieval, storage, and access methods for S&P 500
    constituents and their sector classifications.
    """
    
    def __init__(self, tickers_file="sp500_tickers.csv", sectors_file="sp500_sectors.csv"):
        """
        Initialize the S&P 500 ticker manager.
        
        Args:
            tickers_file (str): Path to file for storing tickers
            sectors_file (str): Path to file for storing sector mappings
        """
        self._tickers_file = tickers_file
        self._sectors_file = sectors_file
        self._tickers = []
        self._sectors = {}
        self._load_data()
    
    def _load_data(self):
        """Load ticker and sector data from files if they exist."""
        # Load tickers
        if os.path.exists(self._tickers_file):
            try:
                df = pd.read_csv(self._tickers_file)
                self._tickers = df['Ticker'].tolist()
            except Exception as e:
                print(f"Error loading tickers file: {e}")
                self._tickers = []
        
        # Load sectors
        if os.path.exists(self._sectors_file):
            try:
                df = pd.read_csv(self._sectors_file)
                self._sectors = {row['Ticker']: row['Sector'] for _, row in df.iterrows()}
            except Exception as e:
                print(f"Error loading sectors file: {e}")
                self._sectors = {}
    
    def refresh_tickers(self, force=False):
        """
        Refresh the S&P 500 ticker list.
        
        Args:
            force (bool): Whether to force refresh even if data exists
            
        Returns:
            bool: Whether the refresh was successful
        """
        if not force and self._tickers and self._sectors:
            print("Using cached S&P 500 data. Use force=True to refresh.")
            return True
        
        try:
            # Wikipedia page with S&P 500 constituents
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            response = requests.get(url)
            
            if response.status_code != 200:
                print(f"Failed to fetch data. Status code: {response.status_code}")
                return False
            
            # Parse the page content
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'class': 'wikitable', 'id': 'constituents'})
            
            if not table:
                print("Could not find S&P 500 constituents table on Wikipedia.")
                return False
            
            # Extract tickers and sectors
            tickers = []
            sectors = {}
            
            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = row.find_all('td')
                if len(cells) >= 2:
                    ticker = cells[0].text.strip()
                    sector = cells[1].text.strip()
                    
                    # Remove trailing "." if present
                    ticker = ticker.replace('.', '')
                    
                    tickers.append(ticker)
                    sectors[ticker] = sector
            
            if not tickers:
                print("No tickers found in the table.")
                return False
            
            # Store the data
            self._tickers = tickers
            self._sectors = sectors
            
            # Save to CSV files
            self._save_data()
            
            print(f"Successfully refreshed S&P 500 data. Found {len(tickers)} tickers.")
            return True
            
        except Exception as e:
            print(f"Error refreshing S&P 500 data: {e}")
            return False
    
    def _save_data(self):
        """Save ticker and sector data to CSV files."""
        # Save tickers
        pd.DataFrame({'Ticker': self._tickers}).to_csv(self._tickers_file, index=False)
        
        # Save sectors
        sector_data = []
        for ticker, sector in self._sectors.items():
            sector_data.append({'Ticker': ticker, 'Sector': sector})
        
        pd.DataFrame(sector_data).to_csv(self._sectors_file, index=False)
        
        print(f"Saved S&P 500 data to {self._tickers_file} and {self._sectors_file}")
    
    def get_tickers(self):
        """Get the list of S&P 500 tickers."""
        return self._tickers
    
    def get_ticker_by_sector(self, sector, limit=None):
        """
        Get tickers for a specific sector.
        
        Args:
            sector (str): The sector name
            limit (int, optional): Maximum number of tickers to return
            
        Returns:
            list: List of tickers in the specified sector
        """
        sector_tickers = [t for t in self._tickers if self._sectors.get(t) == sector]
        
        if limit and len(sector_tickers) > limit:
            return sector_tickers[:limit]
        
        return sector_tickers
    
    def get_sectors(self):
        """Get the list of unique sectors."""
        return sorted(list(set(self._sectors.values())))
    
    def get_sector_for_ticker(self, ticker):
        """Get the sector for a specific ticker."""
        return self._sectors.get(ticker, "Unknown")
    
    def get_random_tickers(self, count=5):
        """Get a random sample of tickers."""
        import random
        if not self._tickers:
            return []
        
        count = min(count, len(self._tickers))
        return random.sample(self._tickers, count)
    
    def get_sector_distribution(self):
        """
        Get the distribution of tickers across sectors.
        
        Returns:
            dict: Dictionary with sector names as keys and counts as values
        """
        distribution = {}
        for sector in self.get_sectors():
            count = len(self.get_ticker_by_sector(sector))
            distribution[sector] = count
        
        return distribution 