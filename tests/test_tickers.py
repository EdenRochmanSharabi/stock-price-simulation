#!/usr/bin/env python3

"""
Test script for S&P 500 ticker data module.
"""

import sys
import os
import unittest

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.tickers import (
    get_sp500_by_sector,
    get_all_tickers,
    get_sample_tickers,
    get_sector_for_ticker
)


class TestTickerData(unittest.TestCase):
    """Test cases for ticker data module."""
    
    def test_get_sp500_by_sector(self):
        """Test getting S&P 500 tickers by sector."""
        sectors = get_sp500_by_sector(use_cache=False)
        
        # Check that we got some sectors
        self.assertTrue(len(sectors) > 0)
        
        # Check that each sector has some tickers
        for sector, tickers in sectors.items():
            self.assertTrue(len(tickers) > 0)
            
            # Check that tickers look valid
            for ticker in tickers:
                self.assertTrue(isinstance(ticker, str))
                self.assertTrue(len(ticker) > 0)
    
    def test_get_all_tickers(self):
        """Test getting all S&P 500 tickers."""
        tickers = get_all_tickers()
        
        # Check that we got some tickers
        self.assertTrue(len(tickers) > 0)
        
        # Check that tickers look valid
        for ticker in tickers:
            self.assertTrue(isinstance(ticker, str))
            self.assertTrue(len(ticker) > 0)
    
    def test_get_sample_tickers(self):
        """Test getting a sample of tickers."""
        sample = get_sample_tickers(count_per_sector=2, min_sectors=3)
        
        # Check that we got some sectors
        self.assertTrue(len(sample) >= 3)
        
        # Check that each sector has exactly 2 tickers
        for sector, tickers in sample.items():
            self.assertTrue(len(tickers) == 2)
    
    def test_get_sector_for_ticker(self):
        """Test getting the sector for a ticker."""
        # Get all sectors
        sectors = get_sp500_by_sector()
        
        # Get a known ticker from a sector
        sector = next(iter(sectors.keys()))
        ticker = sectors[sector][0]
        
        # Check that we get the right sector
        found_sector = get_sector_for_ticker(ticker)
        self.assertEqual(found_sector, sector)


if __name__ == "__main__":
    unittest.main() 