#!/usr/bin/env python3

"""
Test SP500 Ticker Manager
----------------------
Unit tests for the SP500TickerManager class.
"""

from UnitTest.test_base import BaseTestCase
import os
import tempfile
import pandas as pd
from unittest.mock import patch, MagicMock
from stock_sim.utils.sp500 import SP500TickerManager


class TestSP500TickerManager(BaseTestCase):
    """Test cases for the SP500TickerManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create temporary directory for the manager's data files
        self.data_dir = os.path.join(self.temp_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create paths for ticker and sector files
        self.tickers_file = os.path.join(self.data_dir, "sp500_tickers.csv")
        self.sectors_file = os.path.join(self.data_dir, "sp500_sectors.csv")
        
        # Create mock CSV files for testing
        self.create_mock_csv_files()
        
        # Create manager with the specified file paths
        self.manager = SP500TickerManager(
            tickers_file=self.tickers_file,
            sectors_file=self.sectors_file
        )
    
    def create_mock_csv_files(self):
        """Create mock CSV files for testing."""
        # Create mock tickers CSV
        tickers_df = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'GOOG', 'JPM', 'BAC'],
        })
        tickers_df.to_csv(self.tickers_file, index=False)
        
        # Create mock sectors CSV
        sectors_df = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'GOOG', 'JPM', 'BAC'],
            'Sector': ['Technology', 'Technology', 'Technology', 'Finance', 'Finance']
        })
        sectors_df.to_csv(self.sectors_file, index=False)
    
    @patch('requests.get')
    def test_refresh_tickers_with_force(self, mock_get):
        """Test the refresh_tickers method with force=True."""
        # Set up mock response for ticker data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <table id="constituents">
        <tr><th>Symbol</th><th>Security</th><th>GICS Sector</th></tr>
        <tr><td>AAPL</td><td>Apple Inc.</td><td>Technology</td></tr>
        <tr><td>MSFT</td><td>Microsoft Corporation</td><td>Technology</td></tr>
        </table>
        """
        
        # Set up the mock to return response
        mock_get.return_value = mock_response
        
        # Call refresh_tickers with force=True
        self.manager.refresh_tickers(force=True)
        
        # Verify the request was made
        mock_get.assert_called_once()
        
        # Verify the data was updated
        self.assertIn('AAPL', self.manager._tickers)
        self.assertIn('MSFT', self.manager._tickers)
        self.assertEqual(self.manager._sectors.get('AAPL'), 'Technology')
        self.assertEqual(self.manager._sectors.get('MSFT'), 'Technology')
    
    def test_get_tickers(self):
        """Test the get_tickers method."""
        # Ensure the manager has loaded the test data
        self.manager._load_data()
        
        # Get all tickers
        tickers = self.manager.get_tickers()
        
        # Check that all test tickers are returned
        self.assertEqual(set(tickers), {'AAPL', 'MSFT', 'GOOG', 'JPM', 'BAC'})
    
    def test_get_sectors(self):
        """Test the get_sectors method."""
        # Ensure the manager has loaded the test data
        self.manager._load_data()
        
        # Get all sectors
        sectors = self.manager.get_sectors()
        
        # Check that all unique sectors are returned
        self.assertEqual(set(sectors), {'Technology', 'Finance'})
    
    def test_get_ticker_by_sector(self):
        """Test the get_ticker_by_sector method."""
        # Ensure the manager has loaded the test data
        self.manager._load_data()
        
        # Get tickers for Technology sector
        tech_tickers = self.manager.get_ticker_by_sector('Technology')
        
        # Check that all Technology tickers are returned
        self.assertEqual(set(tech_tickers), {'AAPL', 'MSFT', 'GOOG'})
        
        # Get tickers for Finance sector
        finance_tickers = self.manager.get_ticker_by_sector('Finance')
        
        # Check that all Finance tickers are returned
        self.assertEqual(set(finance_tickers), {'JPM', 'BAC'})
        
        # Get tickers for non-existent sector
        nonexistent_tickers = self.manager.get_ticker_by_sector('NonExistent')
        
        # Check that empty list is returned
        self.assertEqual(nonexistent_tickers, [])
    
    def test_get_sector_for_ticker(self):
        """Test the get_sector_for_ticker method."""
        # Ensure the manager has loaded the test data
        self.manager._load_data()
        
        # Get sector for AAPL
        aapl_sector = self.manager.get_sector_for_ticker('AAPL')
        
        # Check that the correct sector is returned
        self.assertEqual(aapl_sector, 'Technology')
        
        # Get sector for non-existent ticker
        nonexistent_sector = self.manager.get_sector_for_ticker('NONEXISTENT')
        
        # Check that 'Unknown' is returned (not None)
        self.assertEqual(nonexistent_sector, 'Unknown')


if __name__ == "__main__":
    unittest.main() 