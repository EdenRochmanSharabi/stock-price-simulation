#!/usr/bin/env python3

"""
Stock Price Simulation Web Server
-------------------------------
Run the stock simulation web server on port 8080.
"""

import sys
import os
from stock_sim.interfaces import run_web_server

if __name__ == "__main__":
    # Get port from command line argument or use default
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}. Using default port 8080.")
    
    # Change to script directory to ensure relative paths work correctly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print(f"Starting Stock Simulation Web Server on port {port}...")
    print(f"Access the API at http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    run_web_server(port=port) 