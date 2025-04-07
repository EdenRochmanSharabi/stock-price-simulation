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

from stock_sim.analysis.reporting import (
    generate_stock_report,
    generate_batch_report
)


class TestReporting(unittest.TestCase):
    """Test cases for reporting module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test outputs
        self.test_dir = tempfile.mkdtemp()
        
        # Mock result data for a stock
        self.stock_result = {
            "ticker": "TEST",
            "model_type": "gbm",
            "initial_price": 100.0,
            "statistics": {
                "expected_return": 10.0,
                "return_volatility": 15.0,
                "var_95": 15.0,
                "var_99": 25.0,
                "max_drawdown": 25.0,
                "sharpe_ratio": 0.67,
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
                }
            },
            "model_params": {
                "mu": 0.08,
                "sigma": 0.2
            },
            "plot_paths": {
                "main": "test_plot.png",
                "histogram": "test_histogram.png"
            }
        }
        
        # Mock batch results
        self.batch_results = {
            "TEST1": {
                "ticker": "TEST1",
                "model_type": "gbm",
                "initial_price": 100.0,
                "statistics": self.stock_result["statistics"],
                "model_params": self.stock_result["model_params"],
                "plot_paths": self.stock_result["plot_paths"]
            },
            "TEST2": {
                "ticker": "TEST2",
                "model_type": "jump",
                "initial_price": 150.0,
                "statistics": self.stock_result["statistics"],
                "model_params": {
                    "mu": 0.08,
                    "sigma": 0.2,
                    "lambda": 5.0,
                    "mu_j": -0.01,
                    "sigma_j": 0.02
                },
                "plot_paths": self.stock_result["plot_paths"]
            }
        }
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_generate_stock_report(self):
        """Test generating a stock report."""
        # Create a mock template file for the test
        template_dir = os.path.join(self.test_dir, "templates")
        os.makedirs(template_dir, exist_ok=True)
        
        with open(os.path.join(template_dir, "stock_report_template.html"), "w") as f:
            f.write("<html>{{ticker}} {{model_type}} {{statistics.expected_return}}</html>")
        
        # Override the template path for testing
        import stock_sim.analysis.reporting as reporting
        original_template_dir = reporting.TEMPLATE_DIR
        reporting.TEMPLATE_DIR = template_dir
        
        try:
            # Generate the report
            report_file = generate_stock_report("TEST", self.stock_result, self.test_dir)
            
            # Check that the file exists
            self.assertTrue(os.path.exists(report_file))
            
            # Check that the file is not empty
            self.assertTrue(os.path.getsize(report_file) > 0)
        finally:
            # Restore the original template dir
            reporting.TEMPLATE_DIR = original_template_dir
    
    def test_generate_batch_report(self):
        """Test generating a batch report."""
        # Create a mock template file for the test
        template_dir = os.path.join(self.test_dir, "templates")
        os.makedirs(template_dir, exist_ok=True)
        
        with open(os.path.join(template_dir, "batch_report_template.html"), "w") as f:
            f.write("<html>Batch report for {{tickers|join(', ')}}</html>")
        
        # Override the template path for testing
        import stock_sim.analysis.reporting as reporting
        original_template_dir = reporting.TEMPLATE_DIR
        reporting.TEMPLATE_DIR = template_dir
        
        try:
            # Generate the report
            report_file = generate_batch_report(self.batch_results, self.test_dir)
            
            # Check that the file exists
            self.assertTrue(os.path.exists(report_file))
            
            # Check that the file is not empty
            self.assertTrue(os.path.getsize(report_file) > 0)
        finally:
            # Restore the original template dir
            reporting.TEMPLATE_DIR = original_template_dir


if __name__ == "__main__":
    unittest.main() 