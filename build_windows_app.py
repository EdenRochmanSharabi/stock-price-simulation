#!/usr/bin/env python3

"""
Build Windows Executable for Stock Simulation App
------------------------------------------------
Creates a standalone Windows executable that can be shared with others.
"""

import os
import subprocess
import sys
import shutil
import platform
from pathlib import Path

def build_windows_executable(force=False):
    """Build a Windows executable using PyInstaller."""
    print("Building Windows executable for Stock Price Simulation App...")
    
    # Check if running on Windows
    if platform.system() != "Windows":
        print("\n⚠️ WARNING: You are not running on Windows!")
        print("PyInstaller creates executables for the platform it's running on.")
        print("Since you're on", platform.system(), "this script will create a", platform.system(), "executable,")
        print("not a Windows executable as intended.\n")
        
        print("Options to build a Windows executable:")
        print("1. Run this script on a Windows machine")
        print("2. Use a Windows virtual machine")
        print("3. Use a continuous integration service (like GitHub Actions) with Windows runners")
        print("4. Use Wine on Linux/macOS (limited compatibility)")
        
        if not force:
            print("\nIf you want to continue anyway, run this script with the --force flag:")
            print("python build_windows_app.py --force")
            return
        
        print("\nContinuing with build process, but the result will be for", platform.system(), "not Windows.\n")
    
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Create directory for the build files
    build_dir = Path("build_windows")
    dist_dir = Path("dist")
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    build_dir.mkdir(exist_ok=True)
    
    # Get absolute paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    run_web_ui_path = os.path.join(current_dir, "run_web_ui.py")
    
    # Check if the entry point file exists
    if not os.path.exists(run_web_ui_path):
        print(f"Error: {run_web_ui_path} not found!")
        return
    
    # Create a spec file for PyInstaller with absolute paths
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    [r'{run_web_ui_path}'],
    pathex=[r'{current_dir}'],
    binaries=[],
    datas=[
        (r'{os.path.join(current_dir, "templates")}', 'templates'),
        (r'{os.path.join(current_dir, "stock_simulation_engine")}', 'stock_simulation_engine'),
        (r'{os.path.join(current_dir, "README_FOR_SHARING.md")}', '.'),
        (r'{os.path.join(current_dir, "requirements.txt")}', '.'),
        (r'{os.path.join(current_dir, "data")}', 'data'),
        (r'{os.path.join(current_dir, "output")}', 'output'),
    ],
    hiddenimports=[
        'flask', 
        'jinja2', 
        'matplotlib.backends.backend_agg',
        'numpy',
        'pandas',
        'matplotlib',
        'seaborn',
        'yfinance',
        'scipy',
        'requests',
        'bs4',
        'lxml',
        'tqdm',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='StockSimulation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StockSimulation',
)
"""
    
    spec_file = os.path.join(current_dir, "StockSimulation.spec")
    with open(spec_file, "w") as f:
        f.write(spec_content)
    
    # Run PyInstaller with the spec file from the current directory
    print("Running PyInstaller...")
    pyinstaller_cmd = [
        sys.executable, 
        "-m", 
        "PyInstaller", 
        "--distpath", 
        str(dist_dir),
        "--workpath", 
        str(build_dir),
        spec_file
    ]
    
    subprocess.check_call(pyinstaller_cmd)
    
    # Create output directories in the distribution
    output_dirs = [
        "data",
        "statistics",
        "graphs",
        "reports",
        "sectors/energy/reports",
        "sectors/utilities/reports",
        "sectors/real_estate/reports",
        "sectors/materials/reports",
        "sectors/technology/reports",
        "sectors/financials/reports",
        "sectors/healthcare/reports",
        "sectors/consumer/reports",
        "sectors/communication/reports",
        "sectors/industrials/reports",
    ]
    
    for outdir in output_dirs:
        os.makedirs(os.path.join(dist_dir, "StockSimulation", "output", outdir), exist_ok=True)
    
    # Create README for the executable
    readme_content = """# Stock Price Simulation App

This is a standalone executable for the Stock Price Simulation application.

## Running the Application

1. Extract all files from the zip archive
2. Double-click on StockSimulation.exe (Windows) or StockSimulation (macOS/Linux)
3. A command window will open and start the application
4. Your web browser should automatically open to http://localhost:8080
5. If the browser doesn't open automatically, manually navigate to http://localhost:8080

## Requirements

- This is a standalone executable and does not require Python to be installed
- Windows 7/8/10/11 (64-bit), macOS 10.13+, or Linux
- Approximately 500MB of disk space
- Internet connection (for downloading stock data)

## Troubleshooting

- If you see a security warning, click "More info" and then "Run anyway"
- If the application fails to start, make sure you've extracted all files from the zip archive
- The application needs an internet connection to download stock data
- If the web interface doesn't load, check if port 8080 is already in use by another application
"""
    
    readme_path = os.path.join(dist_dir, "StockSimulation", "README.txt")
    with open(readme_path, "w") as f:
        f.write(readme_content)
    
    # Determine proper file extension and platform name for the package
    if platform.system() == "Windows":
        platform_name = "Windows"
    elif platform.system() == "Darwin":
        platform_name = "macOS"
    else:
        platform_name = "Linux"
    
    # Zip the distribution
    print("Creating zip archive...")
    zip_filename = f"StockSimulation_{platform_name}"
    zip_path = os.path.join(current_dir, f"{zip_filename}.zip")
    shutil.make_archive(zip_filename, "zip", dist_dir, "StockSimulation")
    
    print("\nBuild completed successfully!")
    print(f"Executable package created: {os.path.abspath(f'{zip_filename}.zip')}")
    print(f"\nThis package is for {platform_name}, not Windows as requested.")
    
    if platform.system() != "Windows":
        print("\nTo create a Windows executable, you need to:")
        print("1. Copy this codebase to a Windows machine")
        print("2. Install Python on that Windows machine")
        print("3. Run this same build script on the Windows machine")
    else:
        print("\nYou can share this zip file with your friends.")
        print("They just need to extract it and run StockSimulation.exe")

if __name__ == "__main__":
    force = "--force" in sys.argv
    build_windows_executable(force) 