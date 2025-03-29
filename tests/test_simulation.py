#!/usr/bin/env python3

"""
Test script for stock price simulation models.
"""

import sys
import os
import unittest
import numpy as np

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.simulation.models import (
    GeometricBrownianMotion,
    RegimeSwitchingModel,
    JumpDiffusionModel,
    CombinedModel
)


class TestSimulationModels(unittest.TestCase):
    """Test cases for simulation models."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ticker = "AAPL"  # Use a reliable ticker for testing
        self.paths = 100
        self.steps = 50
        self.dt = 1/252
        
        # Test with calibration disabled to avoid network requests
        # Also provide a float value for initial_price to avoid pandas Series issues
        self.initial_price = 150.0
        self.gbm_model = GeometricBrownianMotion(self.ticker, calibrate=False, mu=0.08, sigma=0.2)
        self.gbm_model.initial_price = self.initial_price
        
        self.regime_model = RegimeSwitchingModel(self.ticker, calibrate=False)
        self.regime_model.initial_price = self.initial_price
        
        self.jump_model = JumpDiffusionModel(self.ticker, calibrate=False)
        self.jump_model.initial_price = self.initial_price
    
    def test_gbm_simulation(self):
        """Test GBM simulation produces expected output shape."""
        # Run simulation
        paths = self.gbm_model.simulate(paths=self.paths, steps=self.steps, dt=self.dt)
        
        # Check output shape
        self.assertEqual(paths.shape, (self.paths, self.steps + 1))
        
        # Check initial price
        self.assertTrue(np.all(paths[:, 0] == self.initial_price))
        
        # Check all prices are positive
        self.assertTrue(np.all(paths > 0))
    
    def test_regime_simulation(self):
        """Test regime switching simulation produces expected output shape."""
        # Run simulation
        paths = self.regime_model.simulate(paths=self.paths, steps=self.steps, dt=self.dt)
        
        # Check output shape
        self.assertEqual(paths.shape, (self.paths, self.steps + 1))
        
        # Check initial price
        self.assertTrue(np.all(paths[:, 0] == self.initial_price))
        
        # Check all prices are positive
        self.assertTrue(np.all(paths > 0))
    
    def test_jump_simulation(self):
        """Test jump diffusion simulation produces expected output shape."""
        # Run simulation
        paths = self.jump_model.simulate(paths=self.paths, steps=self.steps, dt=self.dt)
        
        # Check output shape
        self.assertEqual(paths.shape, (self.paths, self.steps + 1))
        
        # Check initial price
        self.assertTrue(np.all(paths[:, 0] == self.initial_price))
        
        # Check all prices are positive
        self.assertTrue(np.all(paths > 0))


if __name__ == "__main__":
    unittest.main() 