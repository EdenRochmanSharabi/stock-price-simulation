"""
Interfaces Package
---------------
User interfaces for stock simulation: CLI, API, etc.
"""

from .web_api import main as run_web_server

__all__ = ['run_web_server'] 