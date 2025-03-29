#!/usr/bin/env python3

"""
Test script for reporting module.
"""

import sys
import os
import unittest
import tempfile
import shutil

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.reporting.report_generator import (
    generate_stock_report,
    generate_sector_report,
    generate_master_report
)


class TestReporting(unittest.TestCase):
    """Test cases for reporting module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test outputs
        self.test_dir = tempfile.mkdtemp()
        
        # Mock statistics data for a stock
        self.stock_stats = {
            "ticker": "TEST",
            "initial_price": 100.0,
            "mean_final_price": 110.0,
            "median_final_price": 105.0,
            "std_final_price": 15.0,
            "min_final_price": 70.0,
            "max_final_price": 150.0,
            "percentiles": {
                "1%": 75.0,
                "5%": 85.0,
                "10%": 90.0,
                "25%": 95.0,
                "50%": 105.0,
                "75%": 115.0,
                "90%": 125.0,
                "95%": 135.0,
                "99%": 145.0
            },
            "expected_return": 10.0,
            "median_return": 5.0,
            "var_95": 15.0,
            "var_99": 25.0,
            "prob_profit": 60.0,
            "prob_loss": 40.0,
            "prob_up_10percent": 45.0,
            "prob_up_20percent": 30.0,
            "prob_down_10percent": 25.0,
            "prob_down_20percent": 15.0
        }
        
        # Mock sector results
        self.sector_results = {
            "sectors": {
                "Technology": {
                    "tickers": ["TEST1", "TEST2"],
                    "stats": {
                        "mean_expected_return": 12.5,
                        "std_expected_return": 8.0,
                        "mean_prob_up_20percent": 35.0,
                        "mean_prob_down_20percent": 20.0
                    }
                },
                "Healthcare": {
                    "tickers": ["TEST3", "TEST4"],
                    "stats": {
                        "mean_expected_return": 8.0,
                        "std_expected_return": 12.0,
                        "mean_prob_up_20percent": 25.0,
                        "mean_prob_down_20percent": 30.0
                    }
                }
            }
        }
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_generate_stock_report(self):
        """Test generating a stock report."""
        # Generate the report
        report_file = generate_stock_report("TEST", self.stock_stats, self.test_dir)
        
        # Check that the file exists
        self.assertTrue(os.path.exists(report_file))
        
        # Check that the file is not empty
        self.assertTrue(os.path.getsize(report_file) > 0)
    
    def test_generate_sector_report(self):
        """Test generating a sector report."""
        # Generate the report
        report_file = generate_sector_report(self.sector_results, self.test_dir)
        
        # Check that the file exists
        self.assertTrue(os.path.exists(report_file))
        
        # Check that the file is not empty
        self.assertTrue(os.path.getsize(report_file) > 0)
    
    def test_generate_master_report(self):
        """Test generating a master report."""
        # First generate some stock reports to link to
        generate_stock_report("TEST1", self.stock_stats, self.test_dir)
        generate_stock_report("TEST2", self.stock_stats, self.test_dir)
        
        # Generate the master report
        report_file = generate_master_report(self.test_dir)
        
        # Check that the file exists
        self.assertTrue(os.path.exists(report_file))
        
        # Check that the file is not empty
        self.assertTrue(os.path.getsize(report_file) > 0)


if __name__ == "__main__":
    unittest.main() 