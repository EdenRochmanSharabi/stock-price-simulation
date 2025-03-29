"""
Models Package
-------------
Models for stock price simulation with various approaches.
"""

from .base_model import StockModel, calculate_returns
from .gbm_model import GBMModel
from .jump_diffusion_model import JumpDiffusionModel
from .hybrid_model import HybridModel
from .factory import ModelFactory

__all__ = [
    'StockModel',
    'GBMModel',
    'JumpDiffusionModel', 
    'HybridModel',
    'ModelFactory',
    'calculate_returns'
] 