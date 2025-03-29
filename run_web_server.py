#!/usr/bin/env python3

"""
Stock Price Simulation Web Server
-------------------------------
Run the stock simulation web server on port 8080.
"""

from stock_sim.interfaces import run_web_server

if __name__ == "__main__":
    port = 8080
    print(f"Starting Stock Simulation Web Server on port {port}...")
    print(f"Access the API at http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    run_web_server(port=port) 