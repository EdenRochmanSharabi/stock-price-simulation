#!/usr/bin/env python3

"""
Run All Unit Tests
-----------------
This script runs all unit tests in the UnitTest directory.
Run this file to execute all tests with a single command.
"""

import unittest
import os
import sys

# Add parent directory to path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_all_tests():
    """Discover and run all tests in the UnitTest directory."""
    # Find all test modules in the UnitTest directory
    test_loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    test_suite = test_loader.discover(start_dir, pattern='test_*.py')
    
    # Create a test runner
    test_runner = unittest.TextTestRunner(verbosity=2)
    
    # Run the tests
    result = test_runner.run(test_suite)
    
    # Return success/failure status code
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    print("=" * 70)
    print("Running all unit tests...")
    print("=" * 70)
    sys.exit(run_all_tests()) 