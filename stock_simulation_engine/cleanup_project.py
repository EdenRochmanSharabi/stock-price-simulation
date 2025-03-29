#!/usr/bin/env python3

"""
Cleanup Script for Stock Price Simulation Project
-------------------------------------------------
This script helps remove unnecessary files from the project directory
to clean up the codebase after refactoring.

It will:
1. List all files that will be deleted
2. Ask for confirmation before deletion
3. Create a backup directory with copies of deleted files
"""

import os
import shutil
import sys
from datetime import datetime

# Get the path to the main project directory (one level up)
MAIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(MAIN_DIR, "deleted_files_backup")

# Files to delete (relative to the main project directory)
FILES_TO_DELETE = [
    # Duplicated implementations
    "run_stock_simulation_engine_simulation.py",
    "test_runner.py",
    "test_run.py",
    "main.py",
    
    # Redundant analysis scripts
    "run_sector_simulation.py",
    "run_complete_sp500_analysis.py",
    "stock_simulation_engine_sp500_analysis.py",
    "run_sp500_full.sh",
    "enhanced_sector_analysis.py",
    "run_sector_analysis.py",
    "simple_sector_test.py",
    
    # Temporary/Helper scripts
    "generate_full_script.py",
    "modify_parameters.py",
    "create_script.py",
    "generate_histograms.py",
    "generate_volatile_report.py",
    "simulate_volatile_stocks.py",
    "generate_summary_report.py",
    "generate_report_from_existing_data.py",
    "run_organized_analysis.sh",
    "run_full_sp500_analysis.sh",
    "backtest_simulation.py",
    "find_high_risk_companies.py",
    "generate_report.py",
    "test_yfinance.py",
    
    # Markdown files that might be redundant
    "sp500_analysis_overview.md"
]

# Directories to delete (relative to the main project directory)
# Use caution with these!
DIRS_TO_DELETE = [
    "full_analysis",
    "sp500_full_analysis",
    "sp500_analysis",
    "future",
    "src"
]

# Optional directories that might contain valuable data
OPTIONAL_DIRS = [
    "final_results",
    "results"
]


def create_backup():
    """Create a backup directory for files to be deleted."""
    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{BACKUP_DIR}_{backup_timestamp}"
    os.makedirs(backup_path, exist_ok=True)
    print(f"Created backup directory: {backup_path}")
    return backup_path


def backup_file(file_path, backup_path):
    """Backup a file if it exists."""
    if os.path.exists(file_path):
        # Create necessary subdirectories in the backup
        rel_path = os.path.relpath(file_path, MAIN_DIR)
        backup_file_dir = os.path.dirname(os.path.join(backup_path, rel_path))
        os.makedirs(backup_file_dir, exist_ok=True)
        
        # Copy the file
        try:
            if os.path.isdir(file_path):
                shutil.copytree(file_path, os.path.join(backup_path, rel_path))
            else:
                shutil.copy2(file_path, os.path.join(backup_path, rel_path))
            return True
        except Exception as e:
            print(f"Error backing up {file_path}: {e}")
    return False


def delete_file(file_path):
    """Delete a file or directory if it exists."""
    if os.path.exists(file_path):
        try:
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
    return False


def main():
    """Main function to run the cleanup process."""
    print("\n=== Stock Price Simulation Project Cleanup ===\n")
    print("This script will help clean up unnecessary files after refactoring.")
    print("All deleted files will be backed up first.")
    
    # Get list of files that actually exist
    existing_files = []
    for file_name in FILES_TO_DELETE:
        file_path = os.path.join(MAIN_DIR, file_name)
        if os.path.exists(file_path):
            existing_files.append(file_name)
    
    existing_dirs = []
    for dir_name in DIRS_TO_DELETE:
        dir_path = os.path.join(MAIN_DIR, dir_name)
        if os.path.exists(dir_path):
            existing_dirs.append(dir_name)
    
    existing_optional_dirs = []
    for dir_name in OPTIONAL_DIRS:
        dir_path = os.path.join(MAIN_DIR, dir_name)
        if os.path.exists(dir_path):
            existing_optional_dirs.append(dir_name)
    
    # Print summary
    print("\nFiles to be deleted:")
    for file_name in existing_files:
        print(f"  - {file_name}")
    
    print("\nDirectories to be deleted:")
    for dir_name in existing_dirs:
        print(f"  - {dir_name}/")
    
    print("\nOptional directories that could be deleted (will ask separately):")
    for dir_name in existing_optional_dirs:
        print(f"  - {dir_name}/")
    
    # Ask for confirmation
    if not existing_files and not existing_dirs and not existing_optional_dirs:
        print("\nNo files or directories to delete. Exiting.")
        return
    
    print("\nWARNING: This operation cannot be undone except by restoring from backup.")
    confirm = input("\nDo you want to proceed with deletion? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("Operation cancelled. No files were deleted.")
        return
    
    # Create backup
    backup_path = create_backup()
    
    # Delete files
    deleted_count = 0
    
    # Process regular files
    print("\nDeleting files...")
    for file_name in existing_files:
        file_path = os.path.join(MAIN_DIR, file_name)
        print(f"  - {file_name}: ", end="")
        
        # Backup first
        if backup_file(file_path, backup_path):
            # Then delete
            if delete_file(file_path):
                print("Deleted")
                deleted_count += 1
            else:
                print("Failed to delete")
        else:
            print("Failed to backup, skipping")
    
    # Process mandatory directories
    print("\nDeleting directories...")
    for dir_name in existing_dirs:
        dir_path = os.path.join(MAIN_DIR, dir_name)
        print(f"  - {dir_name}/: ", end="")
        
        # Backup first
        if backup_file(dir_path, backup_path):
            # Then delete
            if delete_file(dir_path):
                print("Deleted")
                deleted_count += 1
            else:
                print("Failed to delete")
        else:
            print("Failed to backup, skipping")
    
    # Process optional directories
    for dir_name in existing_optional_dirs:
        dir_path = os.path.join(MAIN_DIR, dir_name)
        confirm_optional = input(f"\nDelete optional directory '{dir_name}/'? (yes/no): ").strip().lower()
        
        if confirm_optional == "yes":
            print(f"  - {dir_name}/: ", end="")
            
            # Backup first
            if backup_file(dir_path, backup_path):
                # Then delete
                if delete_file(dir_path):
                    print("Deleted")
                    deleted_count += 1
                else:
                    print("Failed to delete")
            else:
                print("Failed to backup, skipping")
    
    # Final report
    print(f"\nCleanup complete. Deleted {deleted_count} files/directories.")
    print(f"Backup created at: {backup_path}")
    print("\nTo restore any deleted files, copy them from the backup directory.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1) 