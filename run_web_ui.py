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

# IMPORTANT: Always use port 8080 for this application
# Port 5000 conflicts with macOS AirPlay Receiver service
# All agents should use port 8080 for consistency

def open_browser():
    """Open browser to the web UI after a short delay."""
    webbrowser.open('http://localhost:8080')

if __name__ == "__main__":
    # Make sure any existing web server is stopped
    try:
        import signal
        import subprocess
        subprocess.run(["pkill", "-f", "python.*run_web"], stderr=subprocess.PIPE)
        time.sleep(1)  # Give servers time to shutdown
    except Exception as e:
        print(f"Note: Could not stop existing servers: {e}")
    
    # Create templates directory if it doesn't exist
    os.makedirs('templates/static', exist_ok=True)
    
    # Ensure absolute paths for templates
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(current_dir, 'templates')
    
    print("\n=== Starting Stock Price Simulation ===")
    print(f"Current directory: {current_dir}")
    print(f"Template directory: {template_dir}")
    
    # Check if index.html exists
    index_path = os.path.join(template_dir, 'index.html')
    if os.path.exists(index_path):
        print(f"Found index.html: {index_path}")
    else:
        print(f"WARNING: index.html not found at {index_path}")
    
    # Force Python to look in current directory first for imports
    sys.path.insert(0, current_dir)
    
    # Set up to open browser after server starts
    Timer(1.5, open_browser).start()
    
    # Import and run the web UI - make sure we're importing the correct one
    import web_interface
    print(f"Imported web_interface from {web_interface.__file__}")
    
    from web_interface import app
    print("Starting web interface for Stock Price Simulation...")
    print("Opening browser to http://localhost:8080")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=8080) 