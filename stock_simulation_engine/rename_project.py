#!/usr/bin/env python3

"""
Rename Script for Stock Price Simulation Project
-----------------------------------------------
Renames files, directories and updates imports to use more descriptive naming
without the 'simplified' prefix.
"""

import os
import re
import shutil
import sys

# Get the current directory (simplified) and parent directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)

# Rename mapping for the directory itself
DIR_RENAME = {
    "simplified": "stock_simulation_engine"
}

# Rename mapping for files
FILE_RENAME = {
    "simplified_simulation.py": "stock_simulation_main.py",
    "run_simulations.py": "run_sector_analysis.py",
    "README_REFACTORED.md": "README.md"
}

# Rename mapping for module files
MODULE_RENAME = {
    "modules/base_models.py": "modules/base.py",
    "modules/simulation_models.py": "modules/models.py",
    "modules/stats_viz.py": "modules/analytics.py",
    "modules/runner.py": "modules/engine.py"
}

# Rename mapping for module imports (from modules.X import Y)
MODULE_IMPORT_RENAME = {
    "base_models": "base",
    "simulation_models": "models", 
    "stats_viz": "analytics",
    "runner": "engine"
}

# Paths that need to be ignored during renaming
IGNORE_PATHS = [
    os.path.abspath(__file__),  # Don't modify this script itself
    os.path.join(CURRENT_DIR, "__pycache__"),
    os.path.join(CURRENT_DIR, "modules", "__pycache__")
]

def update_file_content(file_path, dir_renames, file_renames, module_import_renames):
    """Update the content of a file, replacing renamed imports and paths."""
    
    # Skip if file is in ignore list
    if os.path.abspath(file_path) in IGNORE_PATHS:
        return
    
    # Skip if directory
    if os.path.isdir(file_path):
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace directory name in imports and paths
        modified_content = content
        
        # 1. Replace directory names
        for old_name, new_name in dir_renames.items():
            # Replace various import patterns
            modified_content = re.sub(
                rf'(from|import)\s+{old_name}\.', 
                f'\\1 {new_name}.', 
                modified_content
            )
            
            # Replace paths
            modified_content = modified_content.replace(f'"{old_name}/', f'"{new_name}/')
            modified_content = modified_content.replace(f"'{old_name}/", f"'{new_name}/")
            
            # Replace in docstrings and comments
            modified_content = modified_content.replace(old_name, new_name)
        
        # 2. Replace module imports
        for old_name, new_name in module_import_renames.items():
            # Replace modules in import statements
            modified_content = re.sub(
                rf'(from\s+modules)\.{old_name}(\s+import)', 
                f'\\1.{new_name}\\2', 
                modified_content
            )
            
            # Also replace any direct references to the module names
            modified_content = modified_content.replace(f'modules.{old_name}', f'modules.{new_name}')
        
        # 3. Update class references if needed
        modified_content = modified_content.replace('StockSimulation', 'StockModel')
        
        # Only write if changes were made
        if content != modified_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            print(f"Updated content in: {file_path}")
    
    except Exception as e:
        print(f"Error updating {file_path}: {e}")


def rename_files_and_update_content():
    """Rename files and update import statements in the project."""
    
    # First update all file contents to reflect the new names
    for root, dirs, files in os.walk(CURRENT_DIR):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        
        for filename in files:
            if filename.endswith(('.py', '.md')):
                file_path = os.path.join(root, filename)
                if os.path.abspath(file_path) not in IGNORE_PATHS:
                    update_file_content(file_path, DIR_RENAME, {**FILE_RENAME, **MODULE_RENAME}, MODULE_IMPORT_RENAME)
    
    # Then rename the module files
    for old_rel_path, new_rel_path in MODULE_RENAME.items():
        old_path = os.path.join(CURRENT_DIR, old_rel_path)
        new_path = os.path.join(CURRENT_DIR, new_rel_path)
        
        if os.path.exists(old_path):
            try:
                shutil.move(old_path, new_path)
                print(f"Renamed: {old_path} -> {new_path}")
            except Exception as e:
                print(f"Error renaming {old_path}: {e}")
    
    # Then rename the main files
    for old_name, new_name in FILE_RENAME.items():
        old_path = os.path.join(CURRENT_DIR, old_name)
        new_path = os.path.join(CURRENT_DIR, new_name)
        
        if os.path.exists(old_path):
            try:
                shutil.move(old_path, new_path)
                print(f"Renamed: {old_path} -> {new_path}")
            except Exception as e:
                print(f"Error renaming {old_path}: {e}")


def update_class_names():
    """Update class names in module files to more descriptive ones."""
    # Module specific updates for class names
    class_renames = {
        os.path.join(CURRENT_DIR, "modules/base.py"): [
            ("class StockSimulation", "class StockModel"),
            ("from StockSimulation", "from StockModel")
        ],
        os.path.join(CURRENT_DIR, "modules/models.py"): [
            ("class GeometricBrownianMotion(StockSimulation)", "class GBMModel(StockModel)"),
            ("class JumpDiffusionModel(StockSimulation)", "class JumpDiffusionModel(StockModel)"),
            ("class CombinedModel(StockSimulation)", "class HybridModel(StockModel)"),
            ("GeometricBrownianMotion", "GBMModel"),
            ("CombinedModel", "HybridModel"),
            ("StockSimulation", "StockModel")
        ]
    }
    
    # Update content in each file
    for file_path, replacements in class_renames.items():
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                modified_content = content
                for old_text, new_text in replacements:
                    modified_content = modified_content.replace(old_text, new_text)
                
                if content != modified_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                    print(f"Updated class names in: {file_path}")
            
            except Exception as e:
                print(f"Error updating class names in {file_path}: {e}")


def main():
    """Main function to run the renaming process."""
    print("\n=== Stock Price Simulation Project Renaming ===\n")
    
    # Perform the renaming within the current directory
    rename_files_and_update_content()
    
    # Update class names
    update_class_names()
    
    # Finally, provide instructions for renaming the directory itself
    target_dir = os.path.join(PARENT_DIR, DIR_RENAME["simplified"])
    
    print("\nDirectory renaming instructions:")
    print(f"To complete the process, rename the directory from 'simplified' to '{DIR_RENAME['simplified']}'")
    print(f"You can do this manually or run these commands from your terminal:")
    print(f"\ncd {PARENT_DIR}")
    print(f"mv simplified {DIR_RENAME['simplified']}")
    
    print("\nRenaming process complete for files. Directory renaming requires manual step.")
    print("\nAfter renaming, you may need to update any import statements in files outside this directory.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1) 