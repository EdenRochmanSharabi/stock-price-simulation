# Stock Price Simulation Unit Tests

This directory contains comprehensive unit tests for the Stock Price Simulation application. These tests ensure that all components of the application are working correctly.

## Test Structure

The unit tests are organized by component:

- `test_base.py` - Base test class with common setup and utility methods
- `test_simulation_engine.py` - Tests for the core simulation engine
- `test_stock_models.py` - Tests for stock price models (GBM, Jump Diffusion, Regime Switching, Combined)
- `test_web_interface.py` - Tests for the web interface functions
- `test_sp500_manager.py` - Tests for the S&P 500 ticker manager
- `test_analysis.py` - Tests for analysis and reporting functions

## Running Tests

### Option 1: Run all tests with a single command

Use the provided shell script:

```bash
./run_tests.sh
```

This will run all unit tests and display a summary of the results.

### Option 2: Run tests using Python

Run all tests using the Python test runner:

```bash
python run_all_tests.py
```

### Option 3: Run individual test modules

Run specific test modules:

```bash
python -m unittest UnitTest.test_simulation_engine
python -m unittest UnitTest.test_stock_models
# etc.
```

## Test Methodology

These tests use the Python `unittest` framework and follow these principles:

1. **Isolation** - Tests are isolated from external dependencies using mocks
2. **Performance** - Tests use small sample sizes for quick execution
3. **Coverage** - Tests aim to cover all major functionality
4. **Reliability** - Tests use fixed random seeds where appropriate for deterministic results

## Adding New Tests

To add tests for new functionality:

1. Create a new test file with the naming pattern `test_*.py`
2. Import the `BaseTestCase` class from `test_base.py`
3. Create a test class that extends `BaseTestCase`
4. Add test methods with names starting with `test_`
5. Run the tests to ensure they pass

## Example Test Class

```python
from .test_base import BaseTestCase

class TestNewFeature(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Add additional setup here
    
    def test_new_functionality(self):
        # Test implementation here
        result = some_function()
        self.assertEqual(result, expected_value)
``` 