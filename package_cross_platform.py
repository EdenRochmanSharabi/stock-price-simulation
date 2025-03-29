#!/usr/bin/env python3

"""
Package Stock Simulation App for Cross-Platform Use
-------------------------------------------------
Creates a cross-platform package that can be used on Windows, macOS, or Linux.
This approach requires Python to be installed on the target machine.
"""

import os
import sys
import shutil
import zipfile
from datetime import datetime

def create_cross_platform_package(output_filename=None):
    """Create a cross-platform package of the application."""
    print("Creating cross-platform package for Stock Price Simulation App...")
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create a timestamp for the filename if not provided
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"stock_simulation_app_cross_platform_{timestamp}.zip"
    
    # Create a temporary directory for packaging
    temp_dir = os.path.join(current_dir, "temp_package")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # List of directories to include
        include_dirs = [
            "templates",
            "stock_simulation_engine",
            "data",
            "output"
        ]
        
        # List of files to include
        include_files = [
            "web_interface.py",
            "run_web_ui.py",
            "requirements.txt",
            "README_FOR_SHARING.md"
        ]
        
        # Copy directories
        for dir_name in include_dirs:
            src_path = os.path.join(current_dir, dir_name)
            dst_path = os.path.join(temp_dir, dir_name)
            
            if os.path.exists(src_path):
                print(f"Copying directory: {dir_name}")
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                print(f"Warning: Directory not found: {src_path}")
                # Create empty directory if it doesn't exist
                os.makedirs(dst_path, exist_ok=True)
        
        # Copy files
        for file_name in include_files:
            src_path = os.path.join(current_dir, file_name)
            dst_path = os.path.join(temp_dir, file_name)
            
            if os.path.exists(src_path):
                print(f"Copying file: {file_name}")
                shutil.copy2(src_path, dst_path)
            else:
                print(f"Warning: File not found: {src_path}")
        
        # Create installation and startup scripts for different platforms
        
        # Windows batch file (start.bat)
        windows_script = """@echo off
echo Installing required packages...
pip install -r requirements.txt

echo Starting Stock Price Simulation App...
python run_web_ui.py
"""
        with open(os.path.join(temp_dir, "start.bat"), "w") as f:
            f.write(windows_script)
        
        # Unix shell script (start.sh)
        unix_script = """#!/bin/bash
echo "Installing required packages..."
pip install -r requirements.txt

echo "Starting Stock Price Simulation App..."
python run_web_ui.py
"""
        with open(os.path.join(temp_dir, "start.sh"), "w") as f:
            f.write(unix_script)
        # Make the shell script executable
        os.chmod(os.path.join(temp_dir, "start.sh"), 0o755)
        
        # Create README file
        readme_content = """# Stock Price Simulation App

This is a cross-platform package for the Stock Price Simulation application.

## Requirements

- Python 3.8 or higher
- Internet connection (for downloading stock data and required packages)

## Installation and Running (Windows)

1. Extract all files from the zip archive
2. Double-click on `start.bat`
3. This will install required packages and start the application
4. Your web browser should automatically open to http://localhost:8080
5. If the browser doesn't open automatically, manually navigate to http://localhost:8080

## Installation and Running (macOS/Linux)

1. Extract all files from the zip archive
2. Open a terminal in the extracted directory
3. Make the start script executable if needed: `chmod +x start.sh`
4. Run the script: `./start.sh`
5. This will install required packages and start the application
6. Your web browser should automatically open to http://localhost:8080
7. If the browser doesn't open automatically, manually navigate to http://localhost:8080

## Troubleshooting

- If you get an error about missing Python, make sure Python 3.8+ is installed
- If package installation fails, try running: `pip install --upgrade pip` first
- The application needs an internet connection to download stock data
- If the web interface doesn't load, check if port 8080 is already in use by another application
"""
        
        with open(os.path.join(temp_dir, "README.md"), "w") as f:
            f.write(readme_content)
        
        # Create output subdirectories if they don't exist
        for subdir in ["graphs", "reports"]:
            output_dir = os.path.join(temp_dir, "output", subdir)
            os.makedirs(output_dir, exist_ok=True)
        
        # Create sector output directories
        sectors = ["energy", "utilities", "real_estate", "materials", 
                  "technology", "financials", "healthcare", "consumer", 
                  "communication", "industrials"]
        
        for sector in sectors:
            sector_dir = os.path.join(temp_dir, "output", "sectors", sector, "reports")
            os.makedirs(sector_dir, exist_ok=True)
        
        # Create the zip file
        zip_path = os.path.join(current_dir, output_filename)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from the temp directory
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, rel_path)
        
        print(f"\nPackage created successfully: {output_filename}")
        print(f"Size: {os.path.getsize(zip_path) / 1024 / 1024:.2f} MB")
        
        print("\nThis package can be used on Windows, macOS, or Linux, but requires Python to be installed.")
        print("Windows users need to run start.bat")
        print("macOS/Linux users need to run start.sh")
        
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        create_cross_platform_package(sys.argv[1])
    else:
        create_cross_platform_package() 