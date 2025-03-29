#!/usr/bin/env python3

import os
import sys
print("Script started")

try:
    print("Importing modules...")
    from modules.engine import run_simulation
    from reporting import generate_report
    print("Modules imported successfully")
except Exception as e:
    print(f"Failed to import modules: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def main():
    """Run a simulation for ticker L and generate a report."""
    print("Starting simulation for ticker L...")
    
    # Create output directories
    output_dir = "output"
    print(f"Using output directory: {os.path.abspath(output_dir)}")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    reports_dir = os.path.join(output_dir, "reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
        print(f"Created reports directory: {reports_dir}")
    
    graphs_dir = os.path.join(output_dir, "graphs")
    if not os.path.exists(graphs_dir):
        os.makedirs(graphs_dir)
        print(f"Created graphs directory: {graphs_dir}")
    
    # Run simulation for ticker L
    try:
        print("Running simulation for ticker L...")
        result = run_simulation(
            ticker="L",
            model_type="combined",
            paths=10000,
            steps=21,
            dt=1/252,
            output_dir=output_dir,
            reports_dir=reports_dir,
            graphs_dir=graphs_dir,
            calibrate=True,
            lookback_period="2y"
        )
        
        if result:
            print(f"Simulation completed successfully for ticker L")
            print(f"Check report at: {os.path.abspath(os.path.join(reports_dir, 'L_report.html'))}")
            
            # Generate consolidated report
            print("Generating consolidated report...")
            results_dict = {"L": result}
            generate_report(results_dict, output_dir)
            
            print("All reports generated successfully.")
        else:
            print("Simulation failed for ticker L")
    except Exception as e:
        import traceback
        print(f"Error during simulation: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    print("Running main function...")
    main()
    print("Script completed.") 