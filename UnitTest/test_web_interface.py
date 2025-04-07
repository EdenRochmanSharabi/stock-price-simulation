#!/usr/bin/env python3

"""
Test Web Interface
----------------
Unit tests for the web interface module.
"""

from UnitTest.test_base import BaseTestCase
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
import sys
import web_interface
from flask import Flask


class TestWebInterface(BaseTestCase):
    """Test cases for the web interface."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a test client
        web_interface.app.config['TESTING'] = True
        self.client = web_interface.app.test_client()
        
        # Mock the simulation_status for testing
        self.original_status = web_interface.simulation_status
        web_interface.simulation_status = web_interface.SimulationStatus()
    
    def tearDown(self):
        """Clean up after tests."""
        super().tearDown()
        # Restore original simulation_status
        web_interface.simulation_status = self.original_status
    
    def test_index_route(self):
        """Test the index route returns the main page."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # Check that 'Stock Price Simulation' is in the response
        self.assertIn(b'Stock Price Simulation', response.data)
    
    def test_create_directory(self):
        """Test the create_directory function."""
        test_dir = os.path.join(self.temp_dir, "test_create_dir")
        
        # Directory should not exist initially
        self.assertFalse(os.path.exists(test_dir))
        
        # Create the directory
        result_dir = web_interface.create_directory(test_dir)
        
        # Directory should exist now
        self.assertTrue(os.path.exists(test_dir))
        self.assertEqual(result_dir, test_dir)
        
        # Function should work even if directory already exists
        result_dir2 = web_interface.create_directory(test_dir)
        self.assertEqual(result_dir2, test_dir)
    
    @patch('web_interface.SP500TickerManager')
    def test_get_sector_mapping(self, mock_manager_class):
        """Test the get_sector_mapping function."""
        # Set up mock manager
        mock_manager = MagicMock()
        mock_manager_class.return_value = mock_manager
        
        # Set up the sectors to return
        mock_manager.get_sectors.return_value = ['Technology', 'Finance']
        
        # Set up the tickers for each sector
        mock_manager.get_ticker_by_sector.side_effect = lambda sector: {
            'Technology': ['AAPL', 'MSFT'],
            'Finance': ['JPM', 'BAC']
        }[sector]
        
        # Call the function
        result = web_interface.get_sector_mapping()
        
        # Check the result
        self.assertEqual(result, {
            'Technology': ['AAPL', 'MSFT'],
            'Finance': ['JPM', 'BAC']
        })
        
        # Verify the manager methods were called
        mock_manager.refresh_tickers.assert_called_once_with(force=True)
        mock_manager.get_sectors.assert_called_once()
        self.assertEqual(mock_manager.get_ticker_by_sector.call_count, 2)
    
    @patch('web_interface.generate_stock_report')
    @patch('web_interface.generate_batch_report')
    def test_generate_report(self, mock_batch_report, mock_stock_report):
        """Test the generate_report function."""
        # Set up mock return values
        mock_stock_report.return_value = 'stock_report.html'
        mock_batch_report.return_value = 'batch_report.html'
        
        # Test with single stock report
        result = web_interface.generate_report({'test': 'data'}, 'AAPL', self.temp_dir)
        mock_stock_report.assert_called_once()
        self.assertEqual(result, 'stock_report.html')
        
        # Test with multi stock report
        result = web_interface.generate_report({'test': 'data'}, 'multi_stock', self.temp_dir, is_multi_stock=True)
        mock_batch_report.assert_called_once()
        self.assertEqual(result, 'batch_report.html')
    
    def test_format_price(self):
        """Test the format_price function."""
        self.assertEqual(web_interface.format_price(123.4567), '$123.46')
        self.assertEqual(web_interface.format_price(0), '$0.00')
        with self.assertRaises(TypeError):
            web_interface.format_price(None)
    
    def test_format_percent(self):
        """Test the format_percent function."""
        self.assertEqual(web_interface.format_percent(0.1234), '0.12%')
        self.assertEqual(web_interface.format_percent(0), '0.00%')
        with self.assertRaises(TypeError):
            web_interface.format_percent(None)
    
    def test_format_num(self):
        """Test the format_num function."""
        self.assertEqual(web_interface.format_num(123.4567), '123.4567')
        self.assertEqual(web_interface.format_num(0), '0.0000')
        with self.assertRaises(TypeError):
            web_interface.format_num(None)
    
    def test_simulation_status_class(self):
        """Test the SimulationStatus class."""
        status = web_interface.SimulationStatus()
        
        # Check initial state matches the actual implementation
        initial_status = status.get()
        self.assertIn('running', initial_status)
        self.assertIn('progress', initial_status)
        self.assertEqual(initial_status['progress'], 0)
        
        # Test update
        status.update({
            'running': True,
            'current_stock': 'AAPL',
            'progress': 50
        })
        
        updated_status = status.get()
        self.assertTrue(updated_status['running'])
        self.assertEqual(updated_status['current_stock'], 'AAPL')
        self.assertEqual(updated_status['progress'], 50)
        
        # Test reset
        status.reset()
        reset_status = status.get()
        self.assertFalse(reset_status['running'])
        self.assertEqual(reset_status['progress'], 0)


if __name__ == "__main__":
    unittest.main() 