"""
Analysis Package
--------------
Statistical analysis and data handling for simulation results.
"""

from .statistics import calculate_statistics, calculate_max_drawdown, calculate_max_drawdown_across_paths
from .data_storage import save_simulation_data, cleanup_raw_data
from .reporting import generate_stock_report, generate_batch_report

__all__ = [
    'calculate_statistics',
    'calculate_max_drawdown',
    'calculate_max_drawdown_across_paths',
    'save_simulation_data',
    'generate_stock_report',
    'generate_batch_report',
    'cleanup_raw_data'
] 