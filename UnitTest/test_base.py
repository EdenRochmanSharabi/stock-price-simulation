#!/usr/bin/env python3

"""
Base Test Case
-------------
Base test case class with common setup and helper methods.
"""

import unittest
import os
import sys
import shutil
import tempfile

# Add parent directory to path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class BaseTestCase(unittest.TestCase):
    """Base test case with common setup and teardown for all tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        
        # Common test parameters
        self.test_ticker = "AAPL"  # Use a reliable ticker for testing
        self.test_paths = 10  # Small number for quick tests
        self.test_steps = 5
        self.test_dt = 1/252
        self.test_initial_price = 150.0
        
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory and all its contents
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def get_output_dir(self):
        """Get a subdirectory in the temp directory for outputs."""
        output_dir = os.path.join(self.temp_dir, "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        return output_dir 