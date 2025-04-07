#!/bin/bash

# Change to script's directory
cd "$(dirname "$0")"

# Print header
echo "====================================================="
echo "Running all unit tests for Stock Price Simulation"
echo "====================================================="

# Run all tests using the Python test runner
python run_all_tests.py

# Store exit code
EXIT_CODE=$?

# Print footer
echo "====================================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "All tests passed successfully!"
else
    echo "Some tests failed. Please check the output above."
fi
echo "====================================================="

# Make script executable
chmod +x "$0"

# Return exit code from the test runner
exit $EXIT_CODE 