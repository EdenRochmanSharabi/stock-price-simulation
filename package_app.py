#!/usr/bin/env python3

"""
Package Stock Simulation App
---------------------------
Creates a zip file containing all necessary files for the application.
"""

import os
import sys
import shutil
import zipfile
from datetime import datetime

def create_package(output_filename=None):
    """Create a zip package of the application."""
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(current_dir, "stock_simulation_engine")
    
    # Create a timestamp for the filename if not provided
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"stock_simulation_app_{timestamp}.zip"
    
    # List of directories and files to include
    include_dirs = [
        os.path.join(source_dir, "modules"),
        os.path.join(source_dir, "templates"),
        os.path.join(source_dir, "output"),
    ]
    
    include_files = [
        os.path.join(source_dir, "web_interface.py"),
        os.path.join(source_dir, "run_web_ui.py"),
        os.path.join(source_dir, "run_sector_analysis.py"),
        os.path.join(source_dir, "reporting.py"),
        os.path.join(source_dir, "requirements.txt"),
        os.path.join(current_dir, "README_FOR_SHARING.md"),
    ]
    
    # Create a temporary directory for packaging
    temp_dir = os.path.join(current_dir, "temp_package")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Copy directories
        for src_path in include_dirs:
            if os.path.exists(src_path):
                # Get the directory name (last component of the path)
                dir_name = os.path.basename(src_path)
                dst_path = os.path.join(temp_dir, dir_name)
                
                print(f"Copying directory: {dir_name}")
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                print(f"Warning: Directory not found: {src_path}")
        
        # Copy files
        for src_path in include_files:
            if os.path.exists(src_path):
                # Get the file name (last component of the path)
                file_name = os.path.basename(src_path)
                dst_path = os.path.join(temp_dir, file_name)
                
                print(f"Copying file: {file_name}")
                shutil.copy2(src_path, dst_path)
            else:
                print(f"Warning: File not found: {src_path}")
        
        # Rename README_FOR_SHARING.md to README.md
        if os.path.exists(os.path.join(temp_dir, "README_FOR_SHARING.md")):
            shutil.move(
                os.path.join(temp_dir, "README_FOR_SHARING.md"),
                os.path.join(temp_dir, "README.md")
            )
        
        # Create output subdirectories if they don't exist
        for subdir in ["data", "statistics", "graphs", "reports"]:
            output_dir = os.path.join(temp_dir, "output", subdir)
            os.makedirs(output_dir, exist_ok=True)
        
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
        
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        create_package(sys.argv[1])
    else:
        create_package() 