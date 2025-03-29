#!/usr/bin/env python3

"""
Model Factory
------------
Factory pattern implementation for creating different simulation models.
"""

from .gbm_model import GBMModel
from .jump_diffusion_model import JumpDiffusionModel
from .hybrid_model import HybridModel


class ModelFactory:
    """
    Factory class for creating simulation models.
    
    Implements the Factory design pattern to create different types of
    simulation models with appropriate parameters.
    """
    
    @staticmethod
    def create_model(model_type, ticker, start_date=None, lookback_period="2y", 
                    calibrate=True, mu=None, sigma=None, **kwargs):
        """
        Create a simulation model based on the specified type.
        
        Args:
            model_type (str): Type of model to create ('gbm', 'jump', or 'hybrid')
            ticker (str): Stock ticker symbol
            start_date (datetime, optional): Start date for simulation
            lookback_period (str): Period for historical data
            calibrate (bool): Whether to calibrate model from historical data
            mu (float, optional): Drift parameter (annualized)
            sigma (float, optional): Volatility parameter (annualized)
            **kwargs: Additional parameters specific to model types
            
        Returns:
            StockModel: An instance of the specified model type
            
        Raises:
            ValueError: If the model_type is unknown
        """
        model_type = model_type.lower()
        
        if model_type == 'gbm':
            return GBMModel(ticker, start_date, lookback_period, calibrate, mu, sigma)
            
        elif model_type == 'jump':
            # Extract jump parameters from kwargs with defaults
            jump_intensity = kwargs.get('jump_intensity', 10)
            jump_mean = kwargs.get('jump_mean', -0.01)
            jump_sigma = kwargs.get('jump_sigma', 0.02)
            
            return JumpDiffusionModel(
                ticker, start_date, lookback_period, calibrate, mu, sigma,
                jump_intensity, jump_mean, jump_sigma
            )
            
        elif model_type in ['hybrid', 'combined']:
            # Extract all additional parameters from kwargs with defaults
            jump_intensity = kwargs.get('jump_intensity', 10)
            jump_mean = kwargs.get('jump_mean', -0.01)
            jump_sigma = kwargs.get('jump_sigma', 0.02)
            vol_clustering = kwargs.get('vol_clustering', 0.85)
            
            return HybridModel(
                ticker, start_date, lookback_period, calibrate, mu, sigma,
                vol_clustering, jump_intensity, jump_mean, jump_sigma
            )
            
        else:
            raise ValueError(f"Unknown model type: {model_type}") 