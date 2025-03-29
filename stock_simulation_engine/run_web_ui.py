#!/usr/bin/env python3

"""
Stock Simulation Web UI Launcher
-------------------------------
Launch the web interface for running stock price simulations.
"""

import os
import sys
import webbrowser
import time
from threading import Timer

def open_browser():
    """Open browser to the web UI after a short delay."""
    webbrowser.open('http://localhost:5000')

if __name__ == "__main__":
    # Create templates directory if it doesn't exist
    os.makedirs('templates/static', exist_ok=True)
    
    # Set up to open browser after server starts
    Timer(1.5, open_browser).start()
    
    # Import and run the web UI
    from web_interface import app
    print("Starting web interface for Stock Price Simulation...")
    print("Opening browser to http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=5000) 